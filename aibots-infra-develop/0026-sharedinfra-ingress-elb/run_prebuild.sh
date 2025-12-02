echo "This is for you to prepare the deployment, e.g.: create zip file, sourcecode etc."

cd source/lambda
for D in *; do
    if [ -d "${D}" ]; then
        echo # your processing here
        echo "Packing ${D}"
        
        rm -f ${D}.zip

        cd ${D}
        
        zip -r ../${D}.zip * .[^.]*

        cd ..
    fi
done
