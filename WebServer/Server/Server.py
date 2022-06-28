import socket
import os   
import time 
import select
import colorama

colorama.init()
# Simboli colorati messi in aggunta ai print per evidenziare se siano errori, risultati o altro
text_fault = '\033[31m[!]\033[39m '
text_ok = '\033[32m[+]\033[39m '
text_info = '\033[34m[?]\033[39m '
text_warning = '\033[33m[-]\033[39m '
# L'Ip e la Porta che il server mette in ascolto
UDP_IP = "127.0.0.1"
UDP_PORT = 10000
# Timeout per assumere che i dati in ricezione sono terminati
timeout = 2

# Aprire il socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Faccio il bind nell'ip e nella porta del server
sock.bind((UDP_IP, UDP_PORT))

# Esegue il comando che ha ricevuto
def exec_command(data, address):
    # Testo del server che conferma di aver ricevuto il comando
    print(text_info + "Received command " + data.split()[0] + " from " + address[0])
    # Controlla che comando ha ricevuto e agisce in base ad esso
    if data.split()[0] == 'list':
        # Flag se la directory esiste
        fault_flag = 0
        # Se non viene inviato nulla oltre "list" si guarda nel root del server
        if len(data.split()) == 1: 
            path = "./"
        else: 
            # Salva il percorso inviato nella variabile path eliminando "list"
            path = data.replace("list ", "")
        # Prova a cercare la lista delle directory nella variabile path passata
        # Se viene inviato il percorso di una directory che non esiste o di un file
        # Lancia un'eccezione che viene catturata dal try except
        try:
            # Prende la lista dei file nel path e la spedisce al client
            datasend = ' '.join(os.listdir(path)).encode("latin-1")
            print(text_ok + "Data sent to client")
            sock.sendto(datasend, address)
        except Exception:
            # Messaggio di errore se c'è stato un errore nella ricerca della directory
            error_message = "Error: Directory Path not Found"
            print(text_fault + error_message)
            sock.sendto(error_message.encode(), address)  
        
    elif data.split()[0] == 'get':
        # Controlla se esiste il file nella directory
        if os.path.exists(data[4:]):
            # Prova ad aprire il file e fare il catch della possibile eccezione
            try:
                with open(data[4:], "r") as f:
                    data_file = f.read(4096)
                    # Leggo pari al buffer di ricezione dal file e lo invio al client
                    # Ripeto il ciclo finchè data_file non contiene l'EOF
                    while data_file:
                        sock.sendto(data_file.encode("latin-1"), address)
                        data_file = f.read(4096)
                        # Attendo per dare tempo al client di salvare il file
                        time.sleep(0.5)
                print(text_ok + "File uploaded to client successfully")
            except Exception:
                # Invio un messaggio di errore se trovo il file ma ho problemi ad aprirlo
                error_message = "Something went wrong with the given file (maybe is a directory)"
                print(text_fault + error_message)
                sock.sendto(error_message.encode("latin-1"), address)
        else:
            # Invio un messaggio di errore se non trovo il file
            error_message = "Error: File not Found"
            print(text_fault + error_message)
            sock.sendto(error_message.encode("latin-1"), address)
            
    elif data.split()[0] == 'put':
        # Apro il file e cerco di fare il catch della possibile eccezione
        try:
            # Creo il file o lo apro nella directory di upload del server
            # eliminando da esso il "put"
            if os.path.exists("upload"):
                filepath = "upload/" + data.split('/')[-1].replace("put ", "")
            else:
                filepath = data.split('/')[-1].replace("put ", "")
            with open(filepath, "w") as f:
                while True:
                    # Fino a che ricevo dal client continuo a scrivere sul file
                    ready = select.select([sock], [], [], timeout)
                    if ready[0]:
                        data_file, addr = sock.recvfrom(4096)
                        f.write(data_file.decode("latin-1"))
                    else:
                        break
            # Scrivo l'esito sul server e mando il flag "1" di avvenuto
            # successo al client come risposta
            print(text_ok + "File uploaded to server successfully")
            sock.sendto("1".encode("latin-1"), address)
        except Exception:
            # Faccio la print dell'errore nel server e invio il flag di fallimento al client
            print(text_fault + "Errore while trying to access the file")
            sock.sendto("0".encode("latin-1"), address)
        
    else:
        print(text_fault + "Invalid Command")

# Ciclo che attende la richiesta dal client
while True:
    print('\nWaiting to receive...')
    data, address = sock.recvfrom(4096)
    # Quando riceve la richiesta esegue il comando passandogli come argomento i dati già
    # decodificati e la tupla che contiene l'indirizzo e la porta del client
    exec_command(data.decode("latin-1"), address)