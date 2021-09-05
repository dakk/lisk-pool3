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

import base64
import requests
import json
import sys
import time
import argparse 
from functools import reduce


DEBUG = False
DRY_RUN = False
ONLY_UPDATE = False

NETWORKS = {
	'testnet': '15f0dacc1060e91818224a94286b13aa04279c640bd5d6f193182031d133df7c',
	'mainnet': '4c09e6a781fc4c7bdb936ee815de8f94190f8a7519becd9de2081832be309a99'
}


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

def req(conf, ep):
	uri = conf['apiEndpoint'] + ep
	d = requests.get (uri)
	return d.json ()

r = req

def injectRequestHandler(rr):
	global r
	r = rr

# Parse command line args
def parseArgs():
	global ONLY_UPDATE, DRY_RUN

	parser = argparse.ArgumentParser(description='DPOS delegate pool script')
	parser.add_argument('-c', metavar='config.json', dest='cfile', action='store',
		           default='config.json',
		           help='set a config file (default: config.json)')
	parser.add_argument('-y', dest='alwaysyes', action='store_const',
		           default=False, const=True,
		           help='automatic yes for log saving (default: no)')
	parser.add_argument('--dry-run', dest='dryrun', action='store_const',
		           default=False, const=True,
		           help='dry run (default: no)')
	parser.add_argument('--only-update', dest='onlyupdate', action='store_const',
		           default=False, const=True,
		           help='only update pendings (default: no)')
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

	if args.onlyupdate != None:
		print ("Only updating pendings")
		ONLY_UPDATE = args.onlyupdate
		
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
		print ('Unable to load pool state file. Initializing...')
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
	
	if not conf['includeSelfStake']:
		votes = [x for x in votes if ('username' not in x ) or ('username' in x and x['username'] != conf['delegateName'])]

	# Remove addresses from blacklist
	votes = [x for x in votes if x['address'] not in conf['blackList']]

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
	
	return toPay, pstate, dBlocks
	
def calculateRewards(conf, pstate, votes, pendingRewards):
	for x in votes:
		top = int(pendingRewards * x['percentage'] / 100.)
		addr = x['address']
		
		# If x is the delegate
		if 'username' in x and x['username'] == conf['delegateName']:
			print ('Delegate %s got %.8f lsk of reward' % (x['username'], top / 100000000.))

			if not (addr in pstate['paid']):
				pstate['paid'][addr] = top
			else:
				pstate['paid'][addr] += top
				
		# Otherwise increase pending for the address
		else:
			if not (addr in pstate['pending']):
				pstate['pending'][addr] = top
			else:
				pstate['pending'][addr] += top
	return pstate
	
def payPendings(conf, pstate):
	paylist = []
	
	# For each pending balance, check if meets requirements for payment
	for x in pstate['pending']:
		apend = pstate['pending'][x]

		if (not ONLY_UPDATE) and (apend > int (conf['minPayout'] * 100000000)):
			paylist.append([x, apend])
			
			if not (x in pstate['paid']):
				pstate['paid'][x] = apend
			else:
				pstate['paid'][x] += apend

			pstate['pending'][x] = 0
				
	return pstate, paylist

def paymentCommandForLiskCore(conf, address, amount):
	FEE = '250000'
	cmds = []

	cmds.append('\n #Sending %d to %s' % (amount / 10**8, address))
	cmds.append('TXC=`lisk-core transaction:create 2 0 %s --offline --network %s --network-identifier %s --nonce=\`echo $NONCE\` --passphrase="\`echo $PASSPHRASE\`" --asset=\'{"data": "%s payouts", "amount":%s,"recipientAddress":"%s"}\' | jq .transaction -r`' 
			% (FEE, conf['network'], NETWORKS[conf['network']], conf['delegateName'], amount, addressToBinary(address)))

	if conf['multiSignature']:
		cmds.append('TXC=`lisk-core transaction:sign $TXC --mandatory-keys=$PUB1 --mandatory-keys=$PUB2 --sender-public-key=$PUB1 --passphrase="\`echo $PASSPHRASE\`" | jq .transaction -r`')
		cmds.append('TXC=`lisk-core transaction:sign $TXC --mandatory-keys=$PUB1 --mandatory-keys=$PUB2 --sender-public-key=$PUB1 --passphrase="\`echo $PASSPHRASE2\`"`')

	cmds.append('echo $TXC')
	cmds.append('NONCE=$(($NONCE+1))')
	cmds.append('lisk-core transaction:send `echo $TXC|jq .transaction -r`')

	return '\n'.join(cmds)

	
def savePayments(conf, topay):
	addr = r(conf, 'accounts?username=' + conf['delegateName'])['data'][0]['summary']['address']
	binAddress = addressToBinary(addr)
	
	if 'fromAddress' in conf and (conf['fromAddress']):
		binAddress = addressToBinary(conf['fromAddress'])
		
	st = ['echo Write passphrase: ', 'read PASSPHRASE']

	if conf['multiSignature']:
		st.append('echo Write second passphrase: ')
		st.append('read PASSPHRASE2')

		# Generate pubkey for first and second passphrase, save to variables
		st.append('PUB1="`lisk-core account:get %s | jq .keys.mandatoryKeys[1] -r`"' % (binAddress))
		st.append('PUB2="`lisk-core account:get %s | jq .keys.mandatoryKeys[0] -r`"' % (binAddress))


	# Calculate initial nonce
	st.append('NONCE=`lisk-core account:get %s | jq ".sequence.nonce" -r`' % (binAddress))

	for x in topay:
		st.append(paymentCommandForLiskCore(conf, x[0], x[1]))

	# Rename the file so double payments is avoided
	st.append('mv $0 _$0_done')

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
	rewards, pstate, dBlocks = getForgedSinceLastPayout(conf, pstate)
	
	pendingRewards = int(rewards * conf['sharingPercentage'] / 100.)

	print ('%d produced blocks since last payout, %.8f lsk to pay' % (dBlocks, pendingRewards / 100000000.))	
	
	pstate = calculateRewards(conf, pstate, votes, pendingRewards)
	pstate, topay = payPendings(conf, pstate)
	
	# Show topay
	if len(topay) == 0 and (not ONLY_UPDATE):
		savePoolState(conf, pstate)
		print ('Nothing to pay. Exiting...')
		return

	print('===========')
	for x in topay:
		print('%s => %.8f lsk' % (x[0], x[1] / 100000000.))
	print('===========')
	
	# Ask confirmations for payments
	yes = True
	if conf['interactive'] and (not ONLY_UPDATE):
		yes = input ('Confirm? y/n: ').lower() == 'y'

	if not yes:
		print ('Not confirmed. Aborting...')
		return
		
	# Save payments
	if not ONLY_UPDATE:
		savePayments(conf, topay)
		paidRewards = reduce(lambda x,y: x + int(y[1]), topay, 0)
	
		# Save state
		pstate['history'].append({
			'date': int(time.time()),
			'userPaid': len(topay),
			'rewards': paidRewards
		})
	savePoolState(conf, pstate)

	if DEBUG:
		print (pstate)
	
if __name__ == "__main__":
	try:
		ver = int(requests.get('https://raw.githubusercontent.com/dakk/lisk-pool3/main/VERSION').text)
		if ver > int(open('VERSION', 'r').read()):
			print ('There is a new version of lisk-pool3 available. Please update.')
	except:
		pass
	
	main ()
