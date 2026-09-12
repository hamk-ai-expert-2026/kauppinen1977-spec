# Article Generator and Structured PDF

## Tavoite

Sovellus luo lyhyen suomenkielisen tieteellisen tai teknisen artikkelin PDF-tiedostoksi. Putki on:

`Aihe → Crossref-verkkohaku → lähteet → LM Studio → Pydantic-validointi → PDF`

Crossref on avoin tieteellisten julkaisujen metatietohaku. Ohjelma hakee sieltä lähteiden tekijät, otsikot, vuodet ja DOI-/URL-tiedot. Nämä annetaan LM Studiolle JSON-muotoisena aineistona. Ohjelma hylkää raportin, jos sen lähdeluettelossa on URL, jota Crossref-haku ei palauttanut.

## Vaatimukset

- Windows ja PowerShell
- Python 3.11 tai uudempi (`py`-komento saatavilla)
- LM Studio: paikallinen palvelin käynnissä osoitteessa `http://localhost:1234/v1`
- ladattu chat-malli, esimerkiksi `qwen/qwen3.8-27b`

## Käyttö

1. Avaa PowerShell tässä kansiossa.
2. Käynnistä LM Studion Local Server ja lataa malli.
3. Suorita esimerkiksi:

```powershell
.\run_article_generator.ps1 -Topic "Pilvipalvelujen tietoturva"
```

Ensimmäisellä ajolla PowerShell luo `.venv`-virtuaaliympäristön ja asentaa riippuvuudet. Valmis PDF ja validoitu JSON tallentuvat `output`-kansioon.

Jos LM Studion URL tai mallin nimi poikkeaa oletuksesta:

```powershell
.\run_article_generator.ps1 -Topic "Zero trust -arkkitehtuuri" -LmStudioUrl "http://localhost:1234/v1"
```

## Vertailu ilman verkkohakua

Luo toinen versio samalla aiheella:

```powershell
.\run_article_generator.ps1 -Topic "Pilvipalvelujen tietoturva" -WithoutSearch
```

Tässä vertailuajossa ohjelma ei hyväksy lähteitä ulkoista hakua vasten, koska lähdeaineistoa ei ole. Tarkista tällöin käsin, löytyvätkö tekijä, julkaisun nimi, vuosi ja DOI/URL todella. Tämä osoittaa, miksi maadoitettu versio on luotettavampi: sen lähteet tulevat aidosta hausta ja sovellus tarkistaa URL:t ennen PDF:n luontia.

## Rakenteen validointi

`Report`-Pydantic-malli edellyttää otsikon, tiivistelmän, johdannon, vähintään kaksi pääosiota, johtopäätökset sekä vähintään kaksi lähdettä. Tyhjät kappaleet ja virheellinen JSON keskeyttävät ajon. PDF:n ulkoasu tehdään ReportLabilla, joten kielimalli ei päätä sivutuksesta tai visuaalisesta rakenteesta.

Huomio: Crossrefin metatiedot varmistavat julkaisun viitetiedot, mutta mallin tekemät tulkinnat eivät silti automaattisesti ole tosia. Lähteet ja väitteet pitää arvioida, erityisesti jos aihe on terveydellinen, oikeudellinen tai muuten korkean riskin aihe.
