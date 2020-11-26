import os

print("Looking for log file. This may take a few minutes...")
found = False
for root,dirs,files in os.walk('C:\\Users'):
    if 'Mediatonic' in dirs:
        print("Log file found.")
        found = True
        break

if not found:
    print("couldn't find log path")
    print("please find it and update log_path.txt manually (same format as path in file)")
    print("should be approximately located in a FallGuys_client folder in a Mediatonic folder")
    print("file is called Player.log")
        
log_path = os.path.join(root, 'Mediatonic', 'FallGuys_client', 'Player.log')
print(log_path)

with open("log_path.txt", 'w') as f:
    f.write(log_path)

# if data folder doesn't exist, make it
if not os.path.exists('data'):
    os.makedirs('data')

# if data folder doesn't exist, make it
if not os.path.exists(os.path.join('data', 'archive')):
    os.makedirs(os.path.join('data', 'archive'))