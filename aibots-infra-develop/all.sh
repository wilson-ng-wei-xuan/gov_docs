if [ "$1" == "destroy" ]; then
  DIRs=$(ls -dr $2*[0-9]-*)
  # DIRs=$(ls -dr $2*-*)
else
  DIRs=$(ls -d  $2*[0-9]-*)
  # DIRs=$(ls -d  $2*-*)
fi

for DIR in $DIRs; do
  echo "Processing terraform project: $DIR"
  cd $DIR
  echo "Baseline run* files"
  cp -pr ../run* .
  echo "Running: run.sh $1 $3 $4"
  ../run.sh $1 $3 $4
  if [[ $? == 0 ]]
  then
    echo "[INFO] Success $DIR"
    date
  else
    echo "[ERROR] Broken $DIR"
    date
    exit 1
  fi

  cd ../
done

echo 'grep "Processing terraform project: \|Apply complete! Resources:\|what is the output\|cannot stat" filename'