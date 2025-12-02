COUNTER=1
STATUS="200"
while [ 1 ]; do

  # myRand=`echo $(date +%s%N) | sha256sum | head -c 64`
  myRand='992cd4f430117e876c4d7f140586f5151ac4168a1e8cec8ae1fc9993a6sample'

  STATUS=$(curl -o /dev/null --silent --head --write-out "%{http_code}" https://api.sit.aibots.gov.sg/test_html_response \
  -H "x-atlas-key: $myRand")
  if [[ $STATUS == "200" ]]
  then
    echo "[INFO]  $myRand success $COUNTER"

  else
    echo "[ERROR] $myRand broken $COUNTER"

    exit 1
  fi

  COUNTER=$(($COUNTER+1))

################################################################################

  myRand=`echo $(date +%s%N) | sha256sum | head -c 64`
  # myRand='4995a644a3362d3b060e9634f7d8efa1501815995d237eddc59678f46cc236d7'

  STATUS=$(curl -o /dev/null --silent --head --write-out "%{http_code}" https://api.sit.aibots.gov.sg/test_html_response \
  -H "x-atlas-key: $myRand")
  if [[ $STATUS == "200" ]]
  then
    echo "[INFO]  $myRand success $COUNTER"

  else
    echo "[ERROR] $myRand broken $COUNTER"

    exit 1
  fi

  COUNTER=$(($COUNTER+1))

done