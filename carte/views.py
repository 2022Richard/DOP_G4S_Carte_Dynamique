from django.shortcuts import render
from datetime import datetime
import pandas as pd
from .functions import rapport_alarme
from carte.models import *
from django.contrib import messages
import folium
from folium.plugins import MarkerCluster, Draw
from folium import plugins
from .forms import Formulaire
from django.http import Http404, HttpResponse




# Create your views here. 

def accueil(request): 
    return render(request, 'accueil.html', {'etat':'accueil'})

def contact(request): 
    return render(request, 'contact.html', {'etat':'contact'})

def Mise_a_jour(request): 
    
    if request.method == "POST" : 
        
        file = request.FILES['files']
       
        mon_fichier, test = str(file), False
        type_file = mon_fichier.endswith("xlsx")

        if type_file == False : 
            type_file = mon_fichier.endswith("xls") 

        if type_file == False : 
            messages.error(request,"Ce fichier n'est pas au format excel. Un fichier excel a pour extension xlsx ou xlx. ")
        else : 
            ma_base = pd.read_excel(file)  
            #print( ma_base["Cust Code"] )
            
            if not (("Notepad" in ma_base.columns) or ("Xmit" in ma_base.columns) or ("Despatch" in ma_base.columns) or \
                    ("Vehicle" in ma_base.columns) or ("Arrived" in ma_base.columns) or ("Signal Time" in ma_base.columns) \
                        or ("Sig-Arr Time" in ma_base.columns) or ("Des-ArrTime" in ma_base.columns)) : 
                   
                     messages.error(request,"Ce fichier est au format excel mais pas celui des declenchements alarme.") 
                  
            else :       
                    if not(("custdesc" in ma_base.columns) and ("PhysicalAddress" in ma_base.columns)) :
                    
                        messages.error(request, "Ce fichier est celui des declenchements alarme. \
                               Mais veuillez ajouter les colonnes 'custdesc' et/ou 'PhysicalAddress' puis reessayez !" )
                       
                    else:  test = True
    
            if test == True : 
                # print("to be continued")  

                if 'alarme' in request.POST :  

                    resultat = rapport_alarme(ma_base)  
                    resultat_fin = pd.DataFrame(resultat)
                 
                    res_decl = pd.read_excel("Declenchement.xlsx")
                   
                    frames = [res_decl, resultat_fin]
                    res = pd.concat(frames)

                    duplicate = res[res.duplicated(keep="first")]
                    
                    if duplicate.shape[0] > 0 : 
                        # print("yes")

                         
                        res_clean = res.drop_duplicates()
                       
                        nb_col_clean = res_clean.shape[1] - 15
                        res_clean = res_clean.iloc[:, nb_col_clean :]
                        
                        res_clean.to_excel("Declenchement.xlsx")
                        #print(duplicate) print(res_clean)
                        
                        messages.warning(request, "Mise à jour effectuée avec succès, les doublons ont été supprimés")

                        #print("Yes, présence de doublons")
                    else : 
                        #print("No absence de doublons")     
                        nb_column = res.shape[1] - 15
                        res = res.iloc[:, nb_column :]
                        #print(res)
                        res.to_excel("Declenchement.xlsx")
                       
                        messages.success(request,"Mise à jour effectuée avec succès")
                    
                        
    return render(request, 'mise_a_jour.html', {'etat':'MAP', })       



def carte(request): 
    '''
    form = Formulaire()
    #print("hello")
    if request.method == 'POST':
        print("Ok ok")
        date_heure = request.POST["date_heure"]
        print(date_heure)
        #date = request.POST.get("date")

        if form.is_valid():

            date_heure = form.cleaned_data["date_heure"]
            print(date_heure)

    '''

    map = folium.Map((5.37309, -3.99117), tooltip = "G4S Siege" , zoom_start=7)
    return render(request, 'carte.html', {'etat':'carte', 'map' : map._repr_html_(), })


def carte_actualise_htmx(request, pk) : 
    #choix = pk
    map = folium.Map((5.37309, -3.99117), tooltip = "G4S Siege" , zoom_start=5)
    df = pd.read_excel("Declenchement.xlsx")
    df["DATE_ET_HEURE"] = pd.to_datetime(df['DATE_ET_HEURE'])  # Converti la date au format Y-m-d ou Année, mois, jour
    #print(df.shape)
     
    choix = pk.strip()  

    if "au" in choix :

        date_et_heure_debut = str(choix.partition("au")[0])
        date_et_heure_fin = str(choix.partition("au")[2])

        choix_date = (df["DATE_ET_HEURE"] >= date_et_heure_debut) & (df["DATE_ET_HEURE"] <= date_et_heure_fin)
        choix_clean = df.loc[choix_date]

        #print(choix_clean)

        #coordonnees = pd.DataFrame(list(Coordonnee.objects.all()))
        #print(coordonnees)

        coordonnees_colonne = [{"Cust_Code": x.Cust_Code, "latitude": x.latitude, "longitude": x.longitude} for x in Coordonnee.objects.all()]
        mes_coordonnees = pd.DataFrame(coordonnees_colonne)
        #print(mes_coordonnees) 

        resultat = pd.merge(choix_clean, mes_coordonnees, on='Cust_Code', how="inner")
        #print(resultat)

        resultat['COMMENTAIRE'] = resultat['COMMENTAIRE'].str.lower() # map(lambda x: x.lower())
        resultat_choix = resultat.query('COMMENTAIRE!="test technique" & COMMENTAIRE!="test technicien"') 

        resultat_choix['NOM_ET_ADRESSE_CLIENT'] = resultat_choix['NOM_CLIENT'].astype(str) + ' ' + resultat_choix['ADRESSE_CLIENT'].astype(str)
        resultat_clean = resultat_choix[['TYPE_DECLEN', 'DATE', 'H_RECEPT', 'CODE', 'NOM_ET_ADRESSE_CLIENT', 'NOM_CLIENT', 'ADRESSE_CLIENT', 'latitude', 'longitude']]
        #print(resultat_clean ['NOM_ET_ADRESSE_CLIENT'])

 ########## Affiche la carte ici
        cluster = MarkerCluster(name = "Donnees").add_to(map) 

        # Selection des coordonnées pour la carte
        df_map_2 = resultat_clean[['latitude', 'longitude']]

        # Convertir les colonnes en numerique
        df_map_2 = df_map_2.astype({'latitude':'float','longitude':'float'})

        liste = df_map_2.values.tolist()
        liste_taille = len(liste)

                #map = folium.Map(location=[lat_fixe, long_fixe], zoom_start=4)
        for point in range(0, liste_taille) :  
            html = '''
                    <b> Type declench : </b> {} <br>
                    <b> Date : </b> {} <br>
                    <b> Heure : </b>{} <br>
                    <b> Code Alarme : </b>{} <br>
                    
                '''.format(resultat_clean.iloc[point, 0], resultat_clean.iloc[point, 1],resultat_clean.iloc[point, 2], resultat_clean.iloc[point, 3] )
            popup = folium.Popup(html, max_width=1000)
            marker = folium.Marker(liste[point], popup = popup, tooltip = resultat_clean.iloc[point, 4], icon  = folium.Icon(icon = "cloud"))
            marker.add_to(cluster)

    '''
    else :
        date_et_heure_debut = choix.strip()
        print(date_et_heure_debut) 

        choix_date = (df["DATE"] == date_et_heure_debut) 
        choix_clean = df.loc[choix_date]
        print(choix_clean)
    '''   

    return HttpResponse(f'{map._repr_html_()}') 