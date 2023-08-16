![logot](/images/tosipaikka_logot.png)

# TosiPaikka - GNSS-IMU-UWB Sensor Reader

Sovellus anturidatan lukemiseen GNSS-vastaanottimelta (u-blox C099-F9P), kiihtyvyysanturilta (Xsens MTi-630 AHRS) ja UWB-moduulilta (Decawave DWM1001C). Sovellus on kehitetty toimimaan Raspberry Pi -tietokoneella, mikä mahdollistaa helpon liikkuvuuden kaikkien laitteiden kanssa.

![toimintakaavio](/images/toimintakaavio.png)

Anturidata sisältää seuraavat mittaukset:
* GNSS-vastaanottimen sijainnin pituus- ja leveysasteet
* Gravitaatiovapaat kiihtyvyydet, Eulerin kulmat ja kvaterniot
* UWB-ankkurien ja tunnisteen väliset etäisyysmittaukset ja tunnisteen sijainti.

Anturidatan lukeminen laitteilta tapahtuu omissa säikeissään. Sovelluksessa on lisäksi yksi säie, jossa luetaan dataa GNSS-korjauspalvelusta. Vaihtoehtoina ovat maksullinen u-blox PointPerfect ja ilmainen NTRIP-protokollaan perustuva palvelu rtk2go.com-sivustolla. Korjausdata kirjoitetaan GNSS-vastaanottimeen, mikä parantaa sen paikannustarkkuutta.

Sovellus on kirjoitettu pääasiassa Python-ohjelmointikielellä. Kiihtyvyysanturin *Xsens MT SDK* -ohjelmistokehityspaketin Python-versio ei kuitenkaan ole yhteensopiva Raspberry Pi:n käyttämän ARM-prosessoriarkkitehtuurin kanssa, joten datan lukeminen kiihtyvyysanturilta toteutettiin C++ kielellä tehdyn sovelluksen avulla. C++ sovellus käynnistetään automaattisesti, kun varsinainen anturidatan lukijasovellus käynnistetään.

Luettu anturidata lähetetään MQTT-palvelimelle, jonka kautta muut sovellukset saavat datan käyttöönsä. Mainittakoon vielä erikseen, että tämä sovellus on siis tarkoitettu pelkästään anturidatan lukemiseen. Käyttäjän sijainnin laskemiseen tarvitaan toinen sovellus, joka lukee anturidatan MQTT-palvelimelta.

## Ohjelmistoriippuvuudet

Vaadittavat Python-paketit voidaan asentaa komennolla
```
pip3 install -r requirements.txt
```

Kiihtyvyysanturin lukemista varten Raspberrylle tulee lisäksi asentaa *Xsens MT Manager* -ohjelma. Kiihtyvyysdatan lähetys MQTT-palvelimelle edellyttää myös MQTT C++ Client -kirjaston asennusta.

## Sovelluksen asetukset

### PointPerfect

u-blox PointPerfect -palvelun käyttö edellyttää maksullista tilausta, jonka voi tehdä Thingstream-sivustolla: [https://portal.thingstream.io/](https://portal.thingstream.io/). 

Tee tilauksen teon jälkeen seuraavat toimenpiteet:
* Luo uusi *Location Thing* objekti
* Klikkaa objektia avataksesi sen ominaisuudet
* Kopioi *Details*-välilehdeltä objektin ID-tunnus ja kirjoita se [config.py](/config.py)-tiedostossa olevan *PP_CLIENT_ID*-muuttujan arvoksi
* Lataa *Credentials*-välilehdeltä *pem* (Client Key) ja *crt* (Client Certificate) tiedostot ja kopioi ne sovelluksen *cert* kansioon

### rtk2go.com (NTRIP)

Koodin julkaisuhetkellä datan lukeminen suoraan rtk2go.com-sivustolta ei onnistunut, vaan välissä oli käytettävä paikallisesti asennettua *SNIP NTRIP Caster* ohjelmaa, josta korjausdata saatiin luettua. Kyseisen ohjelman voi ladata ilmaiseksi osoitteesta [https://www.use-snip.com/download/](https://www.use-snip.com/download/). Ohjelman ilmaiskäyttö toimii yhden tunnin kerrallaan. Laskuri nollaantuu, kun ohjelma sammutetaan ja käynnistetään uudestaan.

Korjausdataa lukevassa *NTRIP Client*-ohjelmassa on määritettävä validi sähköpostiosoite käyttäjänimenä, jotta palvelusta voidaan lukea dataa. Sovelluksen NTRIP-asetuksia voi muuttaa [config.py](/config.py)-tiedostossa:

* *NTRIP_HOST*: NTRIP Casterin IP-osoite
* *NTRIP_PORT*: NTRIP Casterin portti
* *NTRIP_AUTH*: validi sähköpostiosoite
* *NTRIP_MOUNTPT*: mountpoint (esim. SeAMK), josta dataa luetaan

Ajantasainen lista tukiasemista (mountpointeista) on näkyvillä alla olevassa osoitteessa.

[http://rtk2go.com:2101/SNIP::STATUS](http://rtk2go.com:2101/SNIP::STATUS)

### Muut asetukset

Määritä sovelluksen käyttämä GNSS-korjausdatapalvelu [config.py](/config.py)-tiedostossa muuttujassa *GNSS_CORRECTION_DATA_SERVICE*. Sallitut arvot ovat *pp* (PointPerfect) tai *ntrip* (rtk2go.com).

Tarkista vielä MQTT-palvelimen IP-osoite tiedostossa [xsens.cpp](/sensors/xsens.cpp). Muista kääntää lähdekoodi, jos teet siihen muutoksia.

## Sovelluksen ajaminen

Sovellus käynnistetään komentokehotteessa suorittamalla komento
```
python3 app.py
```

Sovelluksen ajon voi lopettaa painamalla Ctrl+c.

## Tekijätiedot

Hannu Hakalahti, Asiantuntija TKI, Seinäjoen ammattikorkeakoulu

## Hanketiedot

* Hankkeen nimi: Tosiaikaisen paikkadatan hyödyntäminen teollisuudessa (TosiPaikka)
* Rahoittaja: Etelä-Pohjanmaan liitto
* Aikataulu: 01.12.2021 - 31.08.2023
* Hankkeen kotisivut: [https://projektit.seamk.fi/alykkaat-teknologiat/tosipaikka/](https://projektit.seamk.fi/alykkaat-teknologiat/tosipaikka/)
