# Lisk pool distribution software (v3)

Redistribution software for Lisk delegate on mainnet (and testnet) after the migration to Lisk3. 

**Still WIP, use at your own risk***


## Configuration
Fork this repo; edit config.json and modify the first lines with your settings:

```js
{
	"apiEndpoint": "https://testnet-service.lisk.io/api/v2/",   // Node uri
	"network": "testnet",										// Or mainnet
	"interactive": true,                                        // Ask for confirmation
	"delegateName": "dakk",                                     // Delegate name      
	"sharingPercentage": 15,                                    // % of sharing
	"minPayout": 0.1,                                           // Minimum payout
	"blackList": [],                                            // Addresses to skip
	"poolState": "poollogs.json",                               // Where to save pool state
	"paymentsFile": "payments.sh",                              // Where to save payments commands
	"includeSelfStake": false,                                  // True if we want to include selfstake in distribution calculations
	"multiSignature": false										// True if you're using a multisig account
}
```

## Run

```bash
python liskpool3.py
```

If you want to update pending balances without paying, use ```--only-update``` option


## Frontend

The software has a tiny frontend written in angular. In order to create and update it:

```bash
npm install -g @angular/cli
```

And update with:

```bash
bash update_frontend.sh
```


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

