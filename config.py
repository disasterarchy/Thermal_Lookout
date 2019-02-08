#Use Celsius Units (True) or F (False)
UnitsC = True

#Triggers file name
f_triggers = open('triggers.csv','r')

# URL for IFTTT Maker webhooks
#web_url = 'https://maker.ifttt.com/trigger/{event}/with/key/cxREu7pLkejEkwtCRKMfiA'
try:
    fff = open('web_url.txt','r')
    web_url =  fff.readlines()[0]
    fff.close()
except:
    web_url = 'https://maker.ifttt.com/trigger/{event}/with/key/cxREu7pLkejEkwtCRKMfiA'

# URL for cloud upload
upload_url = 'https://thermal-lookout.appspot.com/upload'

#Keys etc
key = "ahFzfnRoZXJtYWwtbG9va291dHI6CxIHTG9va291dCIWZGVmYXVsdF90aGVybWFsTG9va291dAwLEgpTYXZlZEltYWdlGICAgICA8ogKDA"
your_token = '481eb920-6df8-4ebd-aa63-8d64198833a9'
your_domain = 'thermal-lookout'
img_url = "https://thermal-lookout.appspot.com/img?img_id="
key = "ahFzfnRoZXJtYWwtbG9va291dHI6CxIHTG9va291dCIWZGVmYXVsdF90aGVybWFsTG9va291dAwLEgpTYXZlZEltYWdlGICAgICg55gKDA"
