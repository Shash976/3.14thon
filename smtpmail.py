import smtplib

server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server_ssl.connect("smtp.gmail.com",465)
server_ssl.ehlo()

server_ssl.login("itshashgoel@gmail.com", "superuchihalevidino")

message = "test123"

r = ["shashwat.stanford@gmail.com", "itshashgoel@gmail.com"]
for rn in r:
    server_ssl.sendmail("itshashgoel@gmail.com", rn, message)

server_ssl.quit()