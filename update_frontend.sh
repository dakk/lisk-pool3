direcotry=0
Help()
{
   # Display Help
   echo ""
   echo
   echo "Syntax: [-d|-h]"
   echo "options:"
   echo "d     Specify base directory"
   echo "h     Print this Help."
   echo
}
while getopts d:h flag
do
    case "${flag}" in
        d) directory=${OPTARG};;
        h)
                Help
                exit;;
    esac
done
cp poollogs.json config.json pool-frontend/src/assets/
cd pool-frontend
rm -r ../docs/*
if (( $# == 0 )); then
 
    ng build --base-href=/lisk-pool3/
  else
    ng build --base-href=$directory
fi
cd ..
cp -r pool-frontend/dist/pool-frontend/* docs
