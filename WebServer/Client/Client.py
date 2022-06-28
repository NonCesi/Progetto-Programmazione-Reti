import socket
import select
import os
import time
import colorama

colorama.init()
# Simboli colorati messi in aggunta ai print per evidenziare se siano errori, risultati o altro
text_fault = '\033[31m[!]\033[39m '
text_ok = '\033[32m[+]\033[39m '
text_info = '\033[34m[?]\033[39m '
text_warning = '\033[33m[-]\033[39m '
# L'Ip e la Porta del server
UDP_IP = "127.0.0.1"
UDP_PORT = 10000
# Timeout per assumere che i dati in ricezione sono terminati
timeout = 3
   
# Aprire il socket e server_address conserva l'ip e la porta del server in ascolto
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (UDP_IP, UDP_PORT)

# Funzione per gestire la richiesta di "list"
def list_file(message):
    # Invio la richiesta al server
    sock.sendto(message.encode("latin-1"), server_address)
    # Variabile che unirà i dati ricevuti dal server
    data_full = ""
    while True:
        # Controllo lo stato del socket e, se non avviane uno scambio dati entro un timeout
        # ready sarà false e chiudo la connessione
        ready = select.select([sock], [], [], timeout)
        if ready[0]:
            # Se ready non è false, ricevo dal server con un buffer di 4096
            data, addr = sock.recvfrom(4096)
            data_full += data.decode("latin-1")
        else:
            # Esco dal ciclo se il server non invia dati entro un tempo di timeout
            break
    if data_full == "":
        # Se data è vuoto, non sono stati trovati file
        print(text_warning + "No files found")
    elif data_full == "Error: Directory Path not Found":
        # Se il percorso non è stato trovato
        print(text_fault + data_full)
    else:
        print(text_ok + "Files found:")
        # Stampo una nuova riga per ogni file trovato
        for riga in data_full.split():
            print(riga)
        
# Funzione per gestire la richiesta di "get"
def get_file(message):
    # Invio la richiesta al server
    sock.sendto(message.encode("latin-1"), server_address)
    # Variabile per stampare il progresso di download del file
    bytes_file = 0
    # Richiesta di rinominare il file, qualsiasi valore diverso da y lascerà il file con lo stesso nome
    rename = str(input("Do you want to rename the file? [y/n]: "))
    if rename == "y":
        file_name = str(input("Input new name: "))
    else: 
        file_name = message.split('/')[-1].replace("get ", "")
    # Provo ad aprire il file e fare il catch della possibile eccezione
    try:
        with open(file_name, "w") as f:
            while True:
                # Controllo lo stato del socket e, se non avviane uno scambio dati entro un timeout
                # ready sarà false e chiudo la connessione
                ready = select.select([sock], [], [], timeout)
                if ready[0]:
                    data_file, addr = sock.recvfrom(4096)
                    # Se non trova il file riceverò soltanto il messaggio di errore dal server
                    if data_file.decode("latin-1") == "Error: File not Found" or data_file.decode("latin-1") == "Something went wrong with the given file (maybe is a directory)":
                        print(text_fault + data_file.decode("latin-1"))
                        # Chiudo ed elimino il file vuoto appena creato
                        f.close()
                        os.remove(file_name)
                        break
                    f.write(data_file.decode("latin-1"))
                    bytes_file += len(data_file)
                    print(text_info + "File loaded at %d" %bytes_file, end = "\r")
                else:
                    print(text_ok + "File downloaded successfully")
                    break
    except Exception:
        print(text_fault + "File cannot be opened")

# Funzione per gestire la richiesta di "put"
def put_file(message):
    # Prima di caricare il file sul server, il client deve controllare se il file esiste
    if os.path.exists(message[4:]):
        bytes_file = 0
        # Provo ad aprire il file e fare il catch della possibile eccezione
        try:
            with open(message[4:], "r") as f:
                # Invio al server il comando e il nome del file, 
                # prima di iniziare a mandargli i dati dello stesso
                # dopo che ho cercato di prendere l'eccezione 
                sock.sendto(message.encode("latin-1"), server_address)
                data_file = f.read(4096)
                while data_file:
                    # Invio al server i primi dati del file per poi continuare a ripetere fino all'EOF
                    # Dove si uscirà dal while
                    sock.sendto(data_file.encode("latin-1"), server_address)
                    data_file = f.read(4096)
                    bytes_file += len(data_file)
                    print(text_info + "File uploaded at %d" %bytes_file, end = "\r")
                    # Dò tempo al server di salvare i dati in un nuovo file
                    time.sleep(0.5)
            print(text_info + "Upload complete")
            # Una volta inviato il file attendo un messaggio di esito dal server
            ready = select.select([sock], [], [], 4)
            if ready[0]:
                flag, addr = sock.recvfrom(4096)
                if flag.decode("latin-1") == "1":
                    print(text_ok + "File uploaded successfully")
                else:
                    # Errore per il flag del server
                    print(text_fault + "There was a problem with the upload of the file")
            else:
                # Errore per il timeout della connessione
                print(text_fault + "Connection timeout")
        except Exception:
            # Errore nel file durante l'apertura da parte del client
            print(text_fault + "File cannot be opened")
    else:
        # Errore se non viene trovato il file
         error_message = "Error: File not Found"
         print(text_fault + error_message)

# Ciclo che richiede il comando, controllando che il formato sia corretto
# Per poi procedere a chiamare le funzioni relative ai comandi
while True:
    command = str(input("Enter the command input between list; get; put; exit (to close): "))
    
    # Comando per richiedere la lista di file in una directory
    if command == "list":
        path = str(input("Insert path here: "))
        message = command + " " + path
        list_file(message)
        
    # Comando per richiedere un file da una path del server
    elif command == "get":
        file_req = str(input("Enter the name of the file (path divided with /): "))
        if len(file_req) > 0:
            message = command + " " + file_req
            get_file(message)
        else:
            print(text_fault + "Input a name for the file")
        
    # Comando per inserire un file nella directory di upload del server
    elif command == "put":
        file_req = str(input("Enter the name of the file (path divided with /): "))
        if len(file_req) > 0:
            message = command + " " + file_req
            put_file(message)
        else:
            print(text_fault + "Input a name for the file")
    
    # Comando di uscita per chiudere il client
    elif command == "exit":
        sock.close()
        break;
        
    else:
        print(text_fault + "Invalid command")