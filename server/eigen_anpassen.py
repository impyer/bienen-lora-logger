#!/usr/bin/env python3
# Erzeugt die eigene Server-Fassung aus den Original-Skripten von beelogger.de:
#   python3 server/eigen_anpassen.py <ordner>   (Ordner mit den entpackten M.40-Skripten, wird verändert)
# Jede Änderung prüft, dass die Originalstelle genau einmal vorkommt; sonst Abbruch.
# So lässt sich die Anpassung auf eine neue beelogger-Fassung übertragen und Abweichungen fallen sofort auf.
# Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
import os
import sys

ORDNER = sys.argv[1]
KENNUNG = "eigen-utc-2"

def ersetze(datei, alt, neu, anzahl=1):
    p = os.path.join(ORDNER, datei)
    s = open(p, encoding="utf-8", newline="").read()
    n = s.count(alt)
    if n != anzahl:
        sys.exit("%s: Stelle %d-mal statt %d-mal gefunden:\n%s" % (datei, n, anzahl, alt[:200]))
    s = s.replace(alt, neu)
    open(p, "w", encoding="utf-8", newline="").write(s)

def zeitzone(datei, alt, pfad):
    ersetze(datei, alt,
            "// " + KENNUNG + ": Zeitzone aus beelogger_zeitzone.php (Vorgabe Europe/Berlin)\n"
            "$Zeitzone='Europe/Berlin';\n"
            "if(file_exists(" + pfad + "))include(" + pfad + ");\n"
            "if(!in_array($Zeitzone,timezone_identifiers_list()))$Zeitzone='Europe/Berlin';\n"
            "date_default_timezone_set($Zeitzone);")

# Hilfsfunktion für die Grafik: Zeitspalte aus dem Unix-Zeitstempel (letzte Spalte) als ISO 8601 mit Versatz.
# Damit sind die Zeitpunkte im Browser eindeutig, auch in der doppelten Stunde der Zeitumstellung.
GRAFIKZEILE = r'''
// eigen-utc-1: Zeitspalte für Dygraph aus dem Unix-Zeitstempel (letzte Spalte) als ISO 8601 mit Versatz,
// z. B. 2026-10-25T02:15:00+02:00. Zeilen ohne Zeitstempel bleiben unverändert.
if(!function_exists('bl_grafikzeile')){
function bl_grafikzeile($zeile){
  $zeile=trim($zeile);
  $p=strrpos($zeile,",");$k=strpos($zeile,",");
  if($p===false||$k===false)return $zeile;
  $ts=substr($zeile,$p+1);
  if(!preg_match('/^\d{9,11}$/',$ts))return $zeile;
  return date("Y-m-d\TH:i:sP",(int)$ts).substr($zeile,$k);
}}
'''

# ---------- neue Datei: Zeitzone ----------
open(os.path.join(ORDNER, "beelogger_zeitzone.php"), "w", encoding="utf-8").write(
    "<?php\n"
    "// eigene Server-Fassung (" + KENNUNG + "): Zeitzone für Anzeige, Tag/Nacht-Zeiten, Anmerkungen und CSV-Zeitspalte.\n"
    "// Gespeichert wird intern der Unix-Zeitstempel (UTC, letzte CSV-Spalte); die erste Spalte ist nur Anzeige.\n"
    "// Gültige Namen: https://www.php.net/manual/de/timezones.php\n"
    "$Zeitzone=\"Europe/Berlin\";\n")

# ---------- beelogger_log.php ----------
L = "beelogger1/beelogger_log.php"
zeitzone(L, "date_default_timezone_set('Europe/Berlin');", "'../beelogger_zeitzone.php'")
ersetze(L, '$LORA=0;$NeubeeloggerSketchID="";',
        '$LORA=0;$NeubeeloggerSketchID="";\n'
        '$zeit_unix=null;//eigen-utc-1: Messzeit als Unix-Zeitstempel (UTC), maßgeblich für Speichern und Weitergabe\n'
        '$zeit_utc=(isset($_GET["UTC"])&&$_GET["UTC"]=="1");//eigen-utc-1: EE-Zeiten kommen in UTC (LoRa-Eingang)')
# Empfangszeit: direkt aus time(), ohne Umweg über den Ortszeit-Text
ersetze(L, '$zeit=date("Y/m/d H:i:00");\nif($ext_Passwort==$BeeloggerLogPasswort){',
        '$zeit_unix=time();$zeit_unix-=$zeit_unix%60;//eigen-utc-1: Empfangszeit, Sekunden auf :00 wie bisher\n'
        '$zeit=date("Y/m/d H:i:00",$zeit_unix);\nif($ext_Passwort==$BeeloggerLogPasswort){')
# EE-Datensätze: Zeittext als UTC (mit UTC=1) oder wie bisher als Ortszeit
ersetze(L, "$zeit=$M_D_Arr[$G];$zeit[10]=' ';$zeit[17]='0';$zeit[18]='0';",
        "$zeit=$M_D_Arr[$G];$zeit[10]=' ';$zeit[17]='0';$zeit[18]='0';\n"
        "          if($zeit_utc){//eigen-utc-1: Zeit in UTC -> eindeutiger Zeitstempel, Anzeige in der eingestellten Zeitzone\n"
        "            $zd=DateTime::createFromFormat('Y/m/d H:i:s',$zeit,new DateTimeZone('UTC'));\n"
        "            if($zd){$zeit_unix=$zd->getTimestamp();$zeit=date('Y/m/d H:i:00',$zeit_unix);}else $zeit_unix=null;\n"
        "          }else $zeit_unix=strtotime($zeit);//Ortszeit wie bisher (in der doppelten Stunde nicht eindeutig)")
ersetze(L, "  global $NeubeeloggerSketchID,$M_Type,$M_Name,$M_Sign,$M_Num,$beelg,$zeit,$Softwareversion,",
        "  global $zeit_unix;//eigen-utc-1\n  global $NeubeeloggerSketchID,$M_Type,$M_Name,$M_Sign,$M_Num,$beelg,$zeit,$Softwareversion,")
ersetze(L, "$timestamp=strtotime($zeit);",
        "$timestamp=($zeit_unix!==null)?$zeit_unix:strtotime($zeit);//eigen-utc-1: Zeitstempel nicht aus dem Ortszeit-Text zurückrechnen")

# ---------- beelogger_show.php ----------
S = "beelogger1/beelogger_show.php"
zeitzone(S, "date_default_timezone_set('Europe/Berlin');", "'../beelogger_zeitzone.php'")
ersetze(S, "$Softwareversion = \"M.40\";//vom 03.10.2026 - beelogger_show.php",
        "$Softwareversion = \"M.40\";//vom 03.10.2026 - beelogger_show.php" + GRAFIKZEILE)
ersetze(S, "    for($x=0;$x<$i;$x++){$what=trim($array[$x]);echo '\"'.$what.'\\n\"';if($x<$i-1)echo '+';}",
        "    for($x=0;$x<$i;$x++){$what=bl_grafikzeile($array[$x]);echo '\"'.$what.'\\n\"';if($x<$i-1)echo '+';}//eigen-utc-1")
ersetze(S, '          $DatumAnmerkung=date("Y/m/d H:i:s",$AktualisierungStamp);//Zeitformat für Dygraph umgestellt !$',
        '          $DatumAnmerkung=date("Y-m-d\\TH:i:sP",$AktualisierungStamp);//eigen-utc-1: ISO 8601 mit Versatz, passend zur Datenzeile')

# Xanalyse: Stundengruppen nach dem Unix-Zeitstempel statt nach dem Ortszeit-Text bilden
XAN_ALT = [
    ('$NewArray[$NewCount][0]=date("Y/m/d H",$x[$s-1]);//Datum', '$NewArray[$NewCount][0]=intdiv((int)$x[$s-1],3600)*3600;//eigen-utc-1: volle Stunde als Zeitstempel'),
    ('if(date("Y/m/d H",$x[$s-1])!=$NewArray[$NewCount-1][0]){//Neue Stunde angebrochen', 'if(intdiv((int)$x[$s-1],3600)*3600!=$NewArray[$NewCount-1][0]){//Neue Stunde angebrochen (eigen-utc-1)'),
]
XAN_AUSGABE_ALT = '''  $Output=$val[0].":00,";
  $HelpDate=str_replace("/", "-", $Output);
  for($iV=1;$iV <($Xana);$iV++){
    $Output .=$val[$iV].",";
  }
  $Output .=",,,".strtotime($HelpDate)."\\r\\n";'''
XAN_AUSGABE_NEU = '''  $Output=date("Y/m/d H",(int)$val[0]).":00,";//eigen-utc-1: Anzeige aus dem Zeitstempel
  for($iV=1;$iV <($Xana);$iV++){
    $Output .=$val[$iV].",";
  }
  $Output .=",,,".(int)$val[0]."\\r\\n";//eigen-utc-1: Zeitstempel direkt, nicht aus dem Text'''
XAN_DEMO_ALT = '$LastArray=array(["2022/03/04 05","18.10","","","",""],["2022/03/04 06","18.60","","","",""]);'
XAN_DEMO_NEU = '$LastArray=array([strtotime("2022-03-04 05:00"),"18.10","","","",""],[strtotime("2022-03-04 06:00"),"18.60","","","",""]);//eigen-utc-1'

def xanalyse(datei, einrueck_ausgabe):
    for alt, neu in XAN_ALT:
        ersetze(datei, alt, neu, anzahl=2 if alt.startswith('$NewArray') else 1)
    ersetze(datei, XAN_DEMO_ALT, XAN_DEMO_NEU)
    alt = XAN_AUSGABE_ALT if einrueck_ausgabe is None else einrueck_ausgabe[0]
    neu = XAN_AUSGABE_NEU if einrueck_ausgabe is None else einrueck_ausgabe[1]
    ersetze(datei, alt, neu)
    ersetze(datei, "  asort($NewArray);", "  asort($NewArray);//eigen-utc-1: sortiert jetzt nach Zeitstempel (Zahl)")

xanalyse(S, None)

# ---------- beelogger_sml.php ----------
M = "beelogger1/beelogger_sml.php"
zeitzone(M, "date_default_timezone_set('Europe/Berlin');", "'../beelogger_zeitzone.php'")
open_s = open(os.path.join(ORDNER, M), encoding="utf-8").read()
kopf = [z for z in open_s.split("\n") if z.startswith("$Softwareversion")][0]
ersetze(M, kopf, kopf + GRAFIKZEILE)
ersetze(M, "    for($x=0;$x<$i;$x++){$what=trim($array[$x]);echo '\"'.$what.'\\n\"';if($x<$i-1)echo '+';}",
        "    for($x=0;$x<$i;$x++){$what=bl_grafikzeile($array[$x]);echo '\"'.$what.'\\n\"';if($x<$i-1)echo '+';}//eigen-utc-1")
ersetze(M, '$DatumAnmerkung=date("Y/m/d H:i:s",$AktualisierungStamp);//Zeitformat für Dygraph umgestellt !$',
        '$DatumAnmerkung=date("Y-m-d\\TH:i:sP",$AktualisierungStamp);//eigen-utc-1: ISO 8601 mit Versatz')
sml_s = open(os.path.join(ORDNER, M), encoding="utf-8").read()
i = sml_s.index('strtotime($HelpDate)')
a = sml_s.rindex('$Output=$val[0]', 0, i)
a = sml_s.rindex('\n', 0, a) + 1
e = sml_s.index('\n', i) + 1
alt_block = sml_s[a:e]
neu_block = alt_block.replace('$Output=$val[0].":00,";', '$Output=date("Y/m/d H",(int)$val[0]).":00,";//eigen-utc-1')
neu_block = "\n".join(z for z in neu_block.split("\n") if "$HelpDate=" not in z)
neu_block = neu_block.replace('strtotime($HelpDate)', '(int)$val[0]')
xanalyse(M, (alt_block, neu_block))

# ---------- beelogger_mobileWatch.php ----------
W = "beelogger_mobileWatch.php"
zeitzone(W, "date_default_timezone_set('Europe/Berlin');", "'beelogger_zeitzone.php'")
ersetze(W, "        $PrintArray[$k] = $array[$i]; //Printarray für dygraphs sichern",
        "        $PrintArray[$k] = bl_grafikzeile($array[$i]); //Printarray für dygraphs sichern (eigen-utc-1: ISO-Zeit)")
ersetze(W, '$DatumAnmerkung = date("Y/m/d H:i:s",$AktualisierungStamp);',
        '$DatumAnmerkung = date("Y-m-d\\TH:i:sP",$AktualisierungStamp);//eigen-utc-1')
w_s = open(os.path.join(ORDNER, W), encoding="utf-8").read()
kopf = [z for z in w_s.split("\n") if z.startswith("$Softwareversion")][0]
ersetze(W, kopf, kopf + GRAFIKZEILE)

# ---------- beelogger_mobileCheck.php ----------
zeitzone("beelogger_mobileCheck.php", "date_default_timezone_set('Europe/Berlin');", "'beelogger_zeitzone.php'")

# ---------- beelogger_log.php: externe Ausgabe (BEEP/ThingSpeak) nur für gespeicherte Datensätze (SRV26-05) ----------
# Das Original bereitet die BEEP-/ThingSpeak-Daten vor der Speicherentscheidung vor; ExternDataOut() sendet dann
# auch abgelehnte Datensätze (Duplikat, zu alt). Hier wird der Eintrag zurückgenommen, wenn $store=0 bleibt.
ersetze(L, ' else if($KalibrierTemperatur=="99.9"  AND($timestamp>($akttime+55)))$store=1;\n',
        ' else if($KalibrierTemperatur=="99.9"  AND($timestamp>($akttime+55)))$store=1;\n'
        ' if(!$store){//eigen-utc-2 (SRV26-05): abgelehnten Datensatz nicht an BEEP/ThingSpeak senden\n'
        '   $ExternDataCounter--;\n'
        '   if(is_array($BeepDataArray))foreach(array_keys($BeepDataArray) as $k)unset($BeepDataArray[$k][$ExternDataCounter]);\n'
        '   if(is_array($ThingsPeakDataArray))foreach(array_keys($ThingsPeakDataArray) as $k)unset($ThingsPeakDataArray[$k][$ExternDataCounter]);\n'
        ' }\n')
# Prüfung der BEEP-ID / ThingSpeak-API war immer wahr (OR statt AND): Platzhalter wurden an BEEP gesendet
ersetze(L, '($BeepIdArray[$ib] !="meineID" OR $BeepIdArray[$ib] !="" OR $BeepIdArray[$ib] !="meine BeepID")',
        '($BeepIdArray[$ib] !="meineID" AND $BeepIdArray[$ib] !="" AND $BeepIdArray[$ib] !="meine BeepID")/*eigen-utc-2: AND statt OR*/')
ersetze(L, '($ThingsPeakApiArray[$ib] !="meine Api" OR $ThingsPeakApiArray[$ib] !="")',
        '($ThingsPeakApiArray[$ib] !="meine Api" AND $ThingsPeakApiArray[$ib] !="")/*eigen-utc-2: AND statt OR*/')
# Erkennungsmerkmal für den LoRa-Eingang (SRV26-07): dieser Endpunkt nimmt UTC=1 an
ersetze(L, '$Softwareversion = "M.40";//vom 04.10.2026 - beelogger_log.php\n',
        '$Softwareversion = "M.40";//vom 04.10.2026 - beelogger_log.php\n'
        '$BL_UTC_FAEHIG=1;//eigen-utc-2: Merkmal für den LoRa-Eingang – dieser Endpunkt wertet UTC=1 aus (nicht entfernen)\n')

# ---------- Skripte im Hauptordner ohne Zeitzone (bisher: Vorgabe aus php.ini, oft UTC) ----------
# Sie nutzen date() nur für Anzeigen; die Zeitzone wird direkt nach "<?php" in der ersten Zeile gesetzt.
def zeitzone_kopf(datei):
    p = os.path.join(ORDNER, datei)
    s = open(p, encoding="utf-8", newline="").read()
    zeile = s.split("\n", 1)[0] + "\n"
    if not zeile.startswith("<?php") or "date_default_timezone_set" in s:
        sys.exit("%s: unerwarteter Dateianfang oder Zeitzone schon gesetzt" % datei)
    nl = "\r\n" if zeile.endswith("\r\n") else "\n"
    block = ("// " + KENNUNG + ": Zeitzone aus beelogger_zeitzone.php (Vorgabe Europe/Berlin)" + nl +
             "$Zeitzone='Europe/Berlin';if(file_exists(__DIR__.'/beelogger_zeitzone.php'))include(__DIR__.'/beelogger_zeitzone.php');" + nl +
             "if(!in_array($Zeitzone,timezone_identifiers_list()))$Zeitzone='Europe/Berlin';date_default_timezone_set($Zeitzone);" + nl)
    open(p, "w", encoding="utf-8", newline="").write(zeile + block + s[len(zeile):])

for d in ("beelogger_cron21.php", "scraper.php", "local_Updater.php", "local_Split_Archivnotes.php"):
    zeitzone_kopf(d)

print("eigene Fassung erzeugt (" + KENNUNG + ")")
