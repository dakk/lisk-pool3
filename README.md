# Lisk pool distribution software (v3)

![Test](https://github.com/dakk/lisk-pool3/actions/workflows/python-app.yml/badge.svg)


Redistribution software for Lisk delegate on mainnet (and testnet) after the migration to Lisk3. 

**Use at your own risk, software provided as-is**


## Configuration
Fork this repo; edit config.json and modify the first lines with your settings:

```js
{
	"apiEndpoint": "https://mainnet-service.lisktools.eu/api/v2/",   		// Node uri
	"network": "mainnet",									    // Or testnet
	"interactive": true,                                        // Ask for confirmation
	"delegateName": "dakk",                                     // Delegate name      
	"sharingPercentage": 15,                                    // % of sharing
	"minPayout": 0.1,                                           // Minimum payout
	"blackList": [],                                            // Addresses to skip
	"poolState": "poollogs.json",                               // Where to save pool state
	"paymentsFile": "payments.sh",                              // Where to save payments commands
	"includeSelfStake": false,                                  // True if we want to include selfstake in distribution calculations
	"multiSignature": false,				    // True if you're using a multisig account
	"fromAddress": ""					    // Address from where to make the payments. Remove if the payments will be made from the delegate's address
}
```

## Dependencies

- python3
- requests python module (```pip3 install requests```)
- a synced lisk node

## Run

```bash
python liskpool3.py
```

If you want to update pending balances without paying, use ```--only-update``` option


## Troubleshooting

### Missing genesis_block.json error

If you get this message when you run the payments.sh file:

```
Error: ENOENT: no such file or directory, open 
'/home/lisk/lisk-core/config/mainnet/genesis_block.json'
Error: Missing 1 required arg:
transaction  The transaction to be signed encoded as hex string
```

You can fix it by copying the file ```/home/lisk/.lisk/lisk-core/config/mainnet/genesis_block.json```
to ```/home/lisk/lisk-core/config/mainnet/``` directory

## Frontend

The software has a tiny frontend written in angular. In order to create and update it:

```bash
npm install -g @angular/cli
cd pool-frontend
npm install
```

And update with:

```bash
bash update_frontend.sh [base_directory]
```

Where base directory is the base directory of the frontend (leave blank if it stays in the toplevel).


## License

```
MIT License

Copyright (c) 2021 Davide Gessa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

