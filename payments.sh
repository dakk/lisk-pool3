echo Write passphrase: 
read PASSPHRASE
TXC=`lisk-core transaction:create 2 0 14850014 --passphrase="\`echo $PASSPHRASE\`" --asset='{"data": "Dakk payouts", "amount":14850014,"recipientAddress":"4bda5c909aa1088e80c9921f3c9fedbb1d825a5b"}'`
echo $TXC
lisk-core transaction:send `echo $TXC|jq .transaction -r`
TXC=`lisk-core transaction:create 2 0 148500 --passphrase="\`echo $PASSPHRASE\`" --asset='{"data": "Dakk payouts", "amount":148500,"recipientAddress":"207f89befb647081d94c59c57cb77abb450f5969"}'`
echo $TXC
lisk-core transaction:send `echo $TXC|jq .transaction -r`