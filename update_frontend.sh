cp poollogs.json config.json pool-frontend/src/assets/
cd pool-frontend
rm -r ../docs/*
ng build --base-href=/lisk-pool3/
cd ..
cp -r pool-frontend/dist/pool-frontend/* docs