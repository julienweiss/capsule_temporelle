import os
import RPi.GPIO as GPIO
import time
import threading #threading permet la lecture des fonctions en parallele

num_port_rec = 17 #port sur lequel est connecte le bouton pour lancer l'enregistrement en GPIO.BCM
#num_port_led = 14 #port sur lequel est connecte le la LED temoin en GPIO.BCM /!\ LED inexistante

time_pre_intro = 11 #nombre de secondes avant qu'il soit possible d'annuler le voyage = 11 sec
time_intro = 63 #combien de secondes dure l'intro avant qu'il soit possible de s'exprimer = 63 sec
time_total = 511 #duree totale du fichier generique_capsule_debut.wav = 511 sec
time_outro_annulation = 85 #duree totale du fichier generique_capsule_annulation.wav = 85 sec
time_outro_fin = 95 #duree totale du fichier generique_capsule_fin.wav = 95 sec

timer = 0 #initialisation du timer principal a 0 secondes

chemin_rec = "/media/pi/USB1/" # repertoire de stockage des enregistrements
nom_fichier_rec = "capsuletemporelle"     # nom du fichier pour les enregistrements

start_fiction_debut = False #l'etat True autorise la lecture du fichier generique_capsule_debut.wav
start_fiction_annulation = False #l'etat True autorise la lecture du fichier generique_capsule_annulation.wav
start_fiction_fin = False #l'etat True autorise la lecture du fichier generique_capsule_fin.wav

start_capture = False #l'etat True autorise le lancement d'un enregistrement

start_timer = False #l'etat True autorise le lancement du timer
timer_reinit = False #lorsque = True, reinitialise le timer


GPIO.setmode(GPIO.BCM) #pins GPIO initialises en mode BCM

GPIO.setup(num_port_rec,GPIO.IN)
#GPIO.setup(num_port_led, GPIO.OUT, initial=GPIO.LOW)


def checkFilePath(testString, extension, currentCount): #fonction en charge de la numerotation les enregistrements audio
    if os.path.exists(testString + str(currentCount).zfill(4) + extension):
        return checkFilePath(testString, extension, currentCount+1)
    else:
        return testString + str(currentCount).zfill(4) + extension


def progMain(): #fonction coordinatrice
    global timer
    global timer_reinit
    global start_timer
    global start_fiction_debut
    global start_fiction_annulation
    global start_fiction_fin
    global start_capture
    
    while True:
        if GPIO.input(num_port_rec):
            #securites au cas ou le precedent cycle n'ait pas ete arrete correctement
            os.system("pkill aplay")
            os.system("pkill arecord")
            start_fiction_debut = False
            start_fiction_annulation = False
            start_fiction_fin = False
            start_capture = False
            start_timer = False
            timer_reinit = False
            timer = 0
            #debut du cycle
            start_timer = True # autorise progTimer a lancer le chrono
            start_fiction_debut = True #autorise progAudio a lancer generique_capsule_debut.wav
            start_capture = True #autorise progRecord a debuter un enregistrement
            time.sleep(time_pre_intro) #attend 11 secondes avant de laisser la possiblite a l'utilisateur d'annuler le voyage
            print("il est desormais possible d'annuler")
            while timer <= time_intro: #tant que le timer est inferieur a 63 secondes, lance la sequence d'annulation si le bouton est rappuye
                if GPIO.input(num_port_rec):
                    os.system("pkill aplay") #arret de la lecture de generique_capsule_debut.wav
                    start_fiction_annulation = True #autorise progAudio a debuter la lecture de generique_capsule_annulation.wav
                    time.sleep(time_outro_annulation) #attend 85 secondes (le temps total de l outro annulation) avant d entamer la reinitialisation de la boucle progMain
                    os.system("pkill aplay") #arret de la lecture de generique_capsule_annulation.wav
                    os.system("pkill arecord") #arret de l'enregistrement audio
                    timer_reinit = True #ordonne a progTimer de reinitialiser le timer
                    time.sleep(2)
                    break #retourne au debut de la fonction progMain

            if timer > time_intro: #si le timer est superieur a 63 secondes...
                print("il est desormais possible de retourner dans le present")
                while True:
                    if GPIO.input(num_port_rec) or timer >= time_total: #... lance la sequence de fin si le bouton est rappuye ou si le timer depasse 511 secondes
                        os.system("pkill aplay") #arret de la lecture de generique_capsule_debut.wav
                        start_fiction_fin = True #autorise progAudio a lancer la lecture de generique_capsule_fin.wav
                        time.sleep(time_outro_fin) #attend 95 secondes (le temps total de l'outro fin) avant d'entamer la reinitialisation de la boucle progMain
                        os.system("pkill aplay") #arret de la lecture de generique_capsule_fin.wav
                        os.system("pkill arecord") #arret de l'enregistrement audio
                        timer_reinit = True #ordonne a progTimer de reinitialiser le timer
                        time.sleep(2)
                        break #retourne au debut de la fonction progMain
            
            print("reinitialisation de main")


def progRecord():
    global start_capture
    while True:        
        if start_capture:
            start_capture = False #reinitialise la variable pour le cycle suivant
            #GPIO.output(num_port_led,GPIO.HIGH) #allume la LED
            #print("LED allumee")
            #lancer la procedure d'enregistrement
            nomFichier = checkFilePath( chemin_rec + nom_fichier_rec, ".wav", 0) #lance la fonction checkFilePath (nomme et numerote l'enregistrement dans le repertoire souhaite)
            print("Lancement de l'enregistrement :")
            os.system("arecord -d "+str(time_total)+" -D hw:AK5371,0 -f S16_LE -c2 -r48000 "+nomFichier) #lance l'enregistrement audio et definit ses parametres
            #lorsque arecord est kicked par progMain ou si record egal 511 secondes
            print("enregistrement arrete")
            #GPIO.output(num_port_led,GPIO.LOW) #eteint la lED
            #print("LED eteinte")


def progAudio():
    global start_fiction_debut
    global start_fiction_annulation
    global start_fiction_fin
    
    while True:
        if start_fiction_debut:
            start_fiction_debut = False #reinitialise la variable pour le cycle suivant
            print("lancement de la fiction - generique du debut :")
            os.system("aplay /home/pi/Desktop/generique_capsule_debut.wav") #lance la lecture de generique_capsule_debut.wav
        elif start_fiction_annulation:
            start_fiction_annulation = False #reinitialise la variable pour le cycle suivant
            print("fiction - arret du generique de debut + lancement du son d'annulation :")
            os.system("aplay /home/pi/Desktop/generique_capsule_annulation.wav") #lance la lecture de generique_capsule_annulation.wav
            print("arret de la fiction...")
        elif start_fiction_fin:
            start_fiction_fin = False #reinitialise la variable pour le cycle suivant
            print("fiction - arret du generique de debut + lancement du generique de fin :")
            os.system("aplay /home/pi/Desktop/generique_capsule_fin.wav") #lance la lecture de generique_capsule_fin.wav
            print("arret de la fiction...")
    

def progTimer():
    global timer
    global start_timer
    global timer_reinit
    while True:        
        if start_timer:
            start_timer = False #reinitialise la variable pour le cycle suivant
            while True:
                if not timer_reinit: #tant que timer_reinit = Flase, le timer continue
                    time.sleep(1)
                    timer += 1
                    print("timer : ", timer)
                
                elif timer_reinit: #si timer_reinit = True, le timer arrete de compter et se reinitialise
                    timer_reinit = False #reinitialise la variable pour le cycle suivant
                    timer = 0 #remise a zero du timer
                    print("reinitialisation du timer")
                    break #retourne au debut de la fonction progTimer


start_record = threading.Thread(target=progRecord)
start_audio = threading.Thread(target=progAudio)
start_stopwatch = threading.Thread(target=progTimer)
start_main = threading.Thread(target=progMain)

try:
    print("initialisation...")
    os.system("pkill aplay") #securite au cas ou le script n'ait pas ete arretee normalement
    os.system("pkill arecord") #securite au cas ou le script n'ait pas ete arretee normalement
    time.sleep(1)

    start_record.start()
    start_audio.start()
    start_stopwatch.start()
    start_main.start()
    
    print("pret")

    start_record.join()
    start_audio.join()
    start_stopwatch.join()
    start_main.join()


finally:
    GPIO.cleanup()
    os.system("pkill aplay") #lorsque le script est stoppe, kill tout fichier audio encore en cours
    os.system("pkill arecord") #lorsque le script est stoppe, kill tout enregistrement encore en cours
    print("systeme completement arrete")