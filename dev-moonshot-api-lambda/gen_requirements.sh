pip install pipreqs
pip install pip-tools
# Generate requirements.in based on imports in python file
pipreqs --ignore setup --mode no-pin --savepath requirements.in
# Copy requirements.in to requirements.temp
cp requirements.in requirements.temp
# The requirements.include contains manually added libraries, which are not detected by pipreqs
# Merge it with requirements.in
cat requirements.include >> requirements.temp
# The requirements.exclude contains manually removed libraries, which are to be exculded from requirements.txt
join -v 1 <(sort requirements.temp) <(sort requirements.exclude) > requirements.temp
# Generate requirements.txt using requirements.temp
pip-compile requirements.temp
# Clean up
rm -f requirements.temp requirements.in
