# # This might be deprecated
# # use pyjwt + cryptography
# rm -rf pyjwt[crypto]
# rm -rf pyjwt[crypto]_python3.12.zip
# mkdir pyjwt[crypto]
# cd pyjwt[crypto]
# mkdir -p python/lib/python3.12/site-packages
# pip install pyjwt[crypto] --target python/lib/python3.12/site-packages/
# rm -rf python/lib/python3.12/site-packages/*.dist-info
# zip -r9 ../pyjwt[crypto]_python3.12.zip .
# aws s3 cp ../pyjwt[crypto]_python3.12.zip s3://sst-s3-leon-305326993135/layers/
# cd ../

rm -rf cryptography
rm -rf cryptography_python3.12.zip
mkdir cryptography
cd cryptography
mkdir -p python/lib/python3.12/site-packages
pip install cryptography --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../cryptography_python3.12.zip .
aws s3 cp ../cryptography_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../

rm -rf pyjwt
rm -rf pyjwt_python3.12.zip
mkdir pyjwt
cd pyjwt
mkdir -p python/lib/python3.12/site-packages
pip install pyjwt --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../pyjwt_python3.12.zip .
aws s3 cp ../pyjwt_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../

rm -rf pillow
rm -rf pillow_python3.12.zip
mkdir pillow
cd pillow
mkdir -p python/lib/python3.12/site-packages
pip install pillow --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../pillow_python3.12.zip .
aws s3 cp ../pillow_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../

rm -rf pymongo
rm -rf pymongo_python3.12.zip
mkdir pymongo
cd pymongo
mkdir -p python/lib/python3.12/site-packages
pip install pymongo --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../pymongo_python3.12.zip .
aws s3 cp ../pymongo_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../

rm -rf python-docx
rm -rf python-docx_python3.12.zip
mkdir python-docx
cd python-docx
mkdir -p python/lib/python3.12/site-packages
pip install python-docx --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../python-docx_python3.12.zip .
aws s3 cp ../python-docx_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../

rm -rf pandas
rm -rf pandas_python3.12.zip
mkdir pandas
cd pandas
mkdir -p python/lib/python3.12/site-packages
pip install pandas --target python/lib/python3.12/site-packages/
rm -rf python/lib/python3.12/site-packages/*.dist-info
zip -r9 ../pandas_python3.12.zip .
aws s3 cp ../pandas_python3.12.zip s3://sst-s3-leon-305326993135/layers/
cd ../
