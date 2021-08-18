#!/usr/bin/python

# MIT License

# Copyright (c) 2021 Davide Gessa

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# TODO: handle blacklist

import base64
import requests
import json
import sys
import time
import argparse 
from functools import reduce

DEBUG = False
DRY_RUN = False


if sys.version_info[0] < 3:
	print ('python2 not supported, please use python3')
	sys.exit (0)


def addressToBinary(address):
	B32_STD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
	B32_DICT = "zxvcpmbn3465o978uyrtkqew2adsjhfg"

	s = ''
	for x in address[3::][:-6]:
		s += B32_STD[B32_DICT.index(x)]
	s = base64.b32decode(s)
	return s.hex()

def r(conf, ep):
	uri = conf['apiEndpoint'] + ep
	d = requests.get (uri)
	return d.json ()


# Parse command line args
def parseArgs():
	parser = argparse.ArgumentParser(description='DPOS delegate pool script')
	parser.add_argument('-c', metavar='config.json', dest='cfile', action='store',
		           default='config.json',
		           help='set a config file (default: config.json)')
	parser.add_argument('-y', dest='alwaysyes', action='store_const',
		           default=False, const=True,
		           help='automatic yes for log saving (default: no)')
	parser.add_argument('--dry-run', dest='dryrun', action='store_const',
		           default=False, const=True,
		           help='Dry run (default: no)')
	parser.add_argument('--min-payout', type=float, dest='minpayout', action='store',
		           default=None,
		           help='override the minpayout value from config file')

	args = parser.parse_args ()
		
	# Load the config file
	try:
		conf = json.load (open (args.cfile, 'r'))
	except:
		print ('Unable to load config file.')
		sys.exit ()
		
	# Override minpayout from command line arg
	if args.minpayout != None:
		conf['minPayout'] = args.minpayout

	if args.dryrun != None:
		DRY_RUN = args.dryrun
		
	if args.alwaysyes:
		conf['interactive'] = not args.alwaysyes

	return conf
	
def savePoolState(conf, pstate):
	if DRY_RUN:
		return

	f = open (conf['poolState'], 'w')
	f.write(json.dumps(pstate, indent=4))
	f.close()
	print ('Saved to %s' % (conf['poolState']))

	
def loadPoolState(conf):
	pstate = None
	try:
		pstate = json.load (open (conf['poolState'], 'r'))
	except:
		print ('Unable to load config file. Initializing...')
		pstate = {
			"lastPayout": {
				"date": 0,
				"rewards": 0,
				"producedBlocks": 0
			},
			"pending": {},
			"paid": {},
			"history": []
		}

		if DRY_RUN:
			return pstate

		r = open(conf['poolState'], 'w')
		r.write(json.dumps(pstate))
		r.close()
	return pstate
		
		
def getVotesPercentages(conf):
	votes = r(conf, 'votes_received?limit=100&offset=0&aggregate=true&username=' + conf['delegateName'])['data']['votes']
	totalVotes = reduce(lambda x,y: x + int(y['amount']), votes, 0)

	def votePercentage(v):
		v['percentage'] = int(v['amount']) * 100. / float(totalVotes)
		return v
		
	votes = list(map(votePercentage, votes))
	return votes
	
def getForgedSinceLastPayout(conf, pstate):
	acc = r(conf, 'accounts?username=' + conf['delegateName'])['data'][0]['dpos']['delegate']
	
	toPay = int(acc['rewards']) - int(pstate['lastPayout']['rewards'])
	dBlocks = int(acc['producedBlocks']) - int(pstate['lastPayout']['producedBlocks'])

	if toPay <= 0 or dBlocks <= 0:
		toPay = 0
		dBlocks = 0
	else:
		pstate['lastPayout'] = {
			'date': int (time.time ()),
			'rewards': int(acc['rewards']),
			'producedBlocks': int(acc['producedBlocks'])
		}
	
	print ('%d produced blocks since last payout, %.8f lsk to pay' % (dBlocks, toPay / 100000000.))	
	return toPay, pstate
	
def calculateRewards(conf, pstate, votes, pendingRewards):
	for x in votes:
		top = int(pendingRewards * x['percentage'] / 100.)
		
		if 'username' in x and x['username'] == conf['delegateName']:
			print ('Delegate %s got %.8f lsk of reward' % (x['username'], top / 100000000.))

			if not (x['address'] in pstate['paid']):
				pstate['paid'][x['address']] = top
			else:
				pstate['paid'][x['address']] += top
				
		else:
			if not (x['address'] in pstate['pending']):
				pstate['pending'][x['address']] = top
			else:
				pstate['pending'][x['address']] += top
	return pstate
	
def payPendings(conf, pstate):
	paylist = []
	
	for x in pstate['pending']:
		if pstate['pending'][x] > int (conf['minPayout'] * 100000000):
			paylist.append([x, pstate['pending'][x]])
			
			if not (x in pstate['paid']):
				pstate['paid'][x] = pstate['pending'][x]
			else:
				pstate['paid'][x] += pstate['pending'][x]

			pstate['pending'][x] = 0
				
	return pstate, paylist

def paymentCommandForLiskCore(conf, address, amount):
	FEE = '100000'

	return '\n'.join([
		'TXC=`lisk-core transaction:create 2 0 %s --offline --nonce=\`echo $NONCE\` --passphrase="\`echo $PASSPHRASE\`" --asset=\'{"data": "%s payouts", "amount":%s,"recipientAddress":"%s"}\'`' % (FEE, conf['delegateName'], amount, addressToBinary(address)),
		'echo $TXC',
		'NONCE=$(($NONCE+1))'
		'lisk-core transaction:send `echo $TXC|jq .transaction -r`'
	])

	
def savePayments(conf, topay):
	st = ['echo Write passphrase: ', 'read PASSPHRASE']

	# Calculate initial nonce
	st.append('NONCE=`lisk-core account:get ff417c04e5aefa02d144a326cb94d1b1bdac4cb6 | jq ".sequence.nonce" -r`')

	for x in topay:
		st.append(paymentCommandForLiskCore(conf, x[0], x[1]))

	s = '\n'.join(st)
	
	if DRY_RUN:
		print (s)
	else:
		f = open (conf['paymentsFile'], 'w')
		f.write(s)
		f.close()
	print('Saved to %s' % (conf['paymentsFile']))

def main():
	conf = parseArgs()
	pstate = loadPoolState(conf)
	votes = getVotesPercentages(conf)
	pendingRewards, pstate = getForgedSinceLastPayout(conf, pstate)
	
	pendingRewards = int(pendingRewards * conf['sharingPercentage'] / 100.)
	
	pstate = calculateRewards(conf, pstate, votes, pendingRewards)
	pstate, topay = payPendings(conf, pstate)
	
	# Show topay
	if len(topay) == 0:
		savePoolState(conf, pstate)
		print ('Nothing to pay. Exiting...')
		return

	print('===========')
	for x in topay:
		print('%s => %.8f lsk' % (x[0], x[1] / 100000000.))
	print('===========')
	
	# Ask confirmations for payments
	yes = True
	if conf['interactive']:
		yes = input ('Confirm? y/n: ').lower() == 'y'

	if not yes:
		print ('Not confirmed. Aborting...')
		return
		
	# Save payments
	savePayments(conf, topay)
	
	# Save state
	pstate['history'].append({
		'date': int(time.time()),
		'userPaid': len(topay),
		'rewards': pendingRewards
	})
	savePoolState(conf, pstate)

	if DEBUG:
		print (pstate)
	
if __name__ == "__main__":
	main ()
