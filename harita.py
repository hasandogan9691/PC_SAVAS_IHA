# harita.py


# --- 1. RADARDAKİ ORDUMUZUN SEKTÖREL HARİTASI ---
SEKTOR_HARITASI = {
    "ALTNY": "Teknoloji-Savunma", "ARCLK": "Otomotiv-Sanayi", "ASTOR": "Enerji-Elektrik",
    "AYGAZ": "Enerji-Elektrik", "BIMAS": "Perakende-Gıda", "BRISA": "Otomotiv-Sanayi",
    "CIMSA": "Ağır-Sanayi", "CWENE": "Enerji-Elektrik", "ENJSA": "Enerji-Elektrik",
    "ENKAI": "Holding-İnşaat", "EREGL": "Ağır-Sanayi", "EUPWR": "Enerji-Elektrik",
    "FROTO": "Otomotiv-Sanayi", "GESAN": "Enerji-Elektrik", "KCHOL": "Holding-İnşaat",
    "KORDS": "Otomotiv-Sanayi", "KRDMD": "Ağır-Sanayi", "MAVI": "Perakende-Gıda",
    "MGROS": "Perakende-Gıda", "OYAKC": "Ağır-Sanayi", "PETKM": "Otomotiv-Sanayi",
    "PGSUS": "Ulaştırma-Havacılık", "SAHOL": "Holding-İnşaat", "SISE": "Ağır-Sanayi",
    "TAVHL": "Ulaştırma-Havacılık", "TCELL": "Telekomünikasyon", "THYAO": "Ulaştırma-Havacılık",
    "TOASO": "Otomotiv-Sanayi", "TRALT": "Ulaştırma-Havacılık", "TTKOM": "Telekomünikasyon",
    "TUPRS": "Enerji-Elektrik", "ULKER": "Perakende-Gıda", "VESTL": "Otomotiv-Sanayi",
    "YEOTK": "Enerji-Elektrik"
}
# //[EK] Gelen ham hisse sembollerinin borsa rejimine göre hangi sektörel kümeye ait olduğunu Python hafızasında saniyeler içinde bulan statik sözlük haritası.


# --- 2. ARACI KURUM EMİR WEBHOOK LİNKLERİ ---
PHILLIP_WEBHOOK_HARITASI = {
    "ALTNY": "https://tvwebhook.phc.com.tr/webhook/trade?hash=COlkUhVMolQ3/hEa25GTg7WY96Ayk9pozuaVGiYtNbsohJJH21v5mjXvtB7yEFSGBAJYBXguhInb9yLYApCu8w==",
    "ARCLK": "https://tvwebhook.phc.com.tr/webhook/trade?hash=oocAigjX6fD1YMSYh8YHKudz1CjRejsc24OcC+CR30D9QyHB8aSe/Lu++xGKWUHihBpHsXGEhahQHZMVR5E2Hg==",
    "ASTOR": "https://tvwebhook.phc.com.tr/webhook/trade?hash=XYaLD05T6YZpBocg+WGZh8Eb9fugZIAf2NLxKOtPNdDHBiwRASz3kBkH+Ip8uoqy5of541UQE6gmPMdgmHJlbw==",
    "AYGAZ": "https://tvwebhook.phc.com.tr/webhook/trade?hash=jfClxrdD92a9cUcX0eU+8VC8YzuhypFkgAYO/M+to/YZQODr/GvL/Y/2qQGeEnc19LInuoKpFXA2yaoXclyBJA==",
    "BIMAS": "https://tvwebhook.phc.com.tr/webhook/trade?hash=YQSXxKaax1Ep5BhEtNhKtQzbxLEWI1XNNcahP3DtQrD6L7auOcFv3RAgEoTpauzbj9QVt63dSNPm1XgbijTD4w==",
    "BRISA": "https://tvwebhook.phc.com.tr/webhook/trade?hash=8e+i0AbBST7qC/ro4hv1sCq3atDsC3KKcFVe7bk9fshtGj6eFhH0Bu8/ymPTqYYgU95mvJEXvRu3FY4EnHzMiw==",
    "CIMSA": "https://tvwebhook.phc.com.tr/webhook/trade?hash=ke9wExY2UNfRr70dUCfiZRIMcsD71o5EPNv1Bzt5g6abS8XS5Vw5HVhF+7VXQZbtPLzI0q62N7nyTp2pn8mEoA==",
    "CWENE": "https://tvwebhook.phc.com.tr/webhook/trade?hash=VjYsBnLdweNj9OhIqHorzLUFNmY9lgtFME7nr937kc1pVSqf5H1PI8mK4Fzn6ReFX+ce8KMS/cxsXYVBj1zGoA==",
    "ENJSA": "https://tvwebhook.phc.com.tr/webhook/trade?hash=tTqo9l96BwpmaEz7EJwNTCu/ZSxEzUIycxBCjFVF2Go4njHEeMbJtR2GxmGD30Dq2cty+M4wljfeKz6iXuptTg==",
    "ENKAI": "https://tvwebhook.phc.com.tr/webhook/trade?hash=Pi95MNLuxcSg1yqnyoWpNIxU5uJXJ1wHZxVPbfDNwzESCLoOVt9P18cYZwmTZPvW0lIgh/fEhexwryrGf1INLQ==",
    "EREGL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=U4iBvK+xs2g6+zhk1OIvwgboL8w81rDMaWZVg38DVOgEhGJHXvWDsqjDcFJNVf5J0q79nMbIyZo6CgzxNGVzYg==",
    "EUPWR": "https://tvwebhook.phc.com.tr/webhook/trade?hash=AWhsZ0/xKDyXt6kYV9ARhWhpe+zn6G+Otz1YFhakeK++VpiNFFmMCZrIjgFvPkU1DFnOLCW776qIsXA6CBbSuA==",
    "FROTO": "https://tvwebhook.phc.com.tr/webhook/trade?hash=o+VWOht6zFL+S12f8dmaxc5wMny4071Gra6+9Mb6/m3H34OIFX0i1nvGHOubJsa241uTPG+hCxJ9rqmFuQOLZA==",
    "GESAN": "https://tvwebhook.phc.com.tr/webhook/trade?hash=GRnw+0WXDccfeqlSU0Czj3lMPZqrw4AXnVOX2+jV2zT9hNroApfxAaIwMR7e4wMG9RXXoKte+oaIpdzK5S2w+Q==",
    "KCHOL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=95v3Puqr9kTd39x0PTmd1nZI5Kclv4DNhhk1MfyIS04cNvmIgIr2v5MLoiTBvt4gGYlwmca96mRyRdCRe4eXTA==",
    "KORDS": "https://tvwebhook.phc.com.tr/webhook/trade?hash=4nfunscUe4fsJUIGn46e5VD/3nzZPKut7FRLDCNwLSJbb7TxvTDavLfsMONeg7D6NkZ7mLoricyMpBn4YSPqPA==",
    "KRDMD": "https://tvwebhook.phc.com.tr/webhook/trade?hash=jiG/1DlfcTtiL5pnj3W4DuRV4jVUY5900wJEA1BVIvHRyDu3jqwd8jLeiLaDJVfL7AEFooiBtSA3471wELJHMQ==",
    "MAVI":  "https://tvwebhook.phc.com.tr/webhook/trade?hash=1wFZ5m9JAFBFNPvzj+92L8C7bRK+AooRqsQ2khDf53UzLJvcYRYx6IS4inky2b3JQ3vLu5lE0XMjAHz4x88WUA==",
    "MGROS": "https://tvwebhook.phc.com.tr/webhook/trade?hash=xMxx/vhaXnN98SrVBGIHXJ0L1JgQ24bmoSbyWk8R7xsZ3mGNUo7TvcTIP8x3W5rftAU8s5u6pW1BsuwkevjQbw==",
    "OYAKC": "https://tvwebhook.phc.com.tr/webhook/trade?hash=+QP8N+kqxnwFKNJYftExEFo2juSNMoxT1ZEh8BBLb1Vbh/ej6fFcVkeoBdMxLcd9/AIVPtqNOJTXl36eI/fWXg==",
    "PETKM": "https://tvwebhook.phc.com.tr/webhook/trade?hash=v4n/x/vkhAVzRmC08ydF2JiNfQ57lR6vmjIFF5Avakb+ct7hO/5KL+W2NnQbizZp9eiMcAMhAMV+1Ts1HtOhAQ==",
    "PGSUS": "https://tvwebhook.phc.com.tr/webhook/trade?hash=yCS8V91llRaZ1k84078emYPOMdqCWwxZSPGl5AgepUsx3aW3WOP8Oh5XCX0UVwZGcIX9wtWGHTjQRUikYdgS/A==",
    "SAHOL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=BhGgm8HqeQQ5T28b46w/OXX/+UXqXhPS+Inp4950F4+eV2tczUe8fkx07dqlAO4UIQIBv0UB5b2dhc0c7rxmqA==",
    "SISE":  "https://tvwebhook.phc.com.tr/webhook/trade?hash=q5UlOMxGbNAyZpvBYS3DpXACXaMEvw2QOCcJA+GoxQLIiQN24TOeCIk72HJSbrrOn826PfkLC1/JI3V2/Vs3yw==",
    "TAVHL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=/mdAq+uyrvWfUqE1uzptBw3oDcN7iFo6MTmVLE833R7EeY5q8l3wksKMMhD/XUL4ug9lD4ZcPagujEmPTJD9gQ==",
    "TCELL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=Ug0/Sj+054EzNoEcGJpcwZCyDqBR6oYGDif/67GtyGUET5sfAh2Erjp3FVDq66t7Hw9Uinja2Cwm7pYYAFXoWw==",
    "THYAO": "https://tvwebhook.phc.com.tr/webhook/trade?hash=AB2I+KwvuqUH8HzlWvf89grn5v5tinTMe1tfrwVtcTUc2ypdrds8Qx5gvtgzAZFnY9w++HmmgnbxcoAdwDlz1g==",
    "TOASO": "https://tvwebhook.phc.com.tr/webhook/trade?hash=36vvFaKPLkaw0aftJEWDV7v4qzBvlJ7FAy7gZQ0MExRf6BUSlnIaRGEQqpsUO8Sp71lcOn2TaPVrsTrjrDkL3g==",
    "TRALT": "https://tvwebhook.phc.com.tr/webhook/trade?hash=C5/QCRv4u200mDARz1COxTc/hMX3kejGvG+G/K26DEnLYXAuW3XjaMwY2SQd41yniNLrk78ojy7sjouzi6ARQw==",
    "TTKOM": "https://tvwebhook.phc.com.tr/webhook/trade?hash=nGYev5oXCbef7NZ4a9vTyXNuTkpx7fcK5+fGQNO3lmsqp+RwvXs3DMB631tWWQEfHGZVWzEU2oAWXc72VqSqGQ==",
    "TUPRS": "https://tvwebhook.phc.com.tr/webhook/trade?hash=HRlvlwdS3ryLbRI8GVJaIp3Jo3S4ENRkb5+JyxJrfBBRqF94no3ig5DlSslGGD4o2dS6Gpx2FgRPNJJqdVkqoQ==",
    "ULKER": "https://tvwebhook.phc.com.tr/webhook/trade?hash=/cHQJe2PtdaZ7KeTT9jMc4CND+NceztWDZZgyil0Adm9J63szk5l7xkvTzUnxu1CXxFTDt0f2W/CZZvpB9JUJQ==",
    "VESTL": "https://tvwebhook.phc.com.tr/webhook/trade?hash=xBjSwmJqC1PsIGudkdNL1zv5ZpvBT6p3ztAVYzXjdBNAgzKAujoSMGBrHGuHCdG1sGdSECK1qeGmG2ls+XvBag==",
    "YEOTK": "https://tvwebhook.phc.com.tr/webhook/trade?hash=mJKdsUF1f9qexuzGxhXDgCjMrfjM9deeF1AbnFPAsrVRwFjdCzVCZlZvJ6DtY+e4gV28PeMGflzrDxW007jUqQ=="
}
# //[EK] broker.py dosyasının onaylanan sinyalleri Phillip Capital bünyesinde doğru tahtaya yönlendirebilmesi için her hisseye özel atanmış olan emir API adresleri sözlüğü.
