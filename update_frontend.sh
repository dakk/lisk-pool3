cp poollogs.json config.json pool-frontend/src/assets/
cd pool-frontend
ng build
cd ..
cp -r pool-frontend/dist/pool-frontend/* docs