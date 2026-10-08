<?php
/*
 *(C)2024 Jeremias Bruker, Thorsten Gurzan, Rudolf Schick - beelogger.de
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option)any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses>.
*/
//   beelogger.de - Arduino Datenlogger für Imker
//   Erläuterungen dieses Programmcodes unter https://beelogger.de


$Softwareversion = "M.40";//vom 03.10.2026 - beelogger_show.php
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

$show_version=0;//0, 1, 2 Programmertool

header('Content-Type: text/html; charset=UTF-8');

SESSION_START();

$isHttps=(!empty($_SERVER['HTTPS']));
if($isHttps==0){
 $local_network="192.168.178.";
 if((strstr($_SERVER['REMOTE_ADDR'],$local_network)==false)&&(strstr($_SERVER['SERVER_NAME'],$local_network)==false)){
?>
<!DOCTYPE html>
<html lang="de">
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<link rel="shortcut icon" href="./../beelogger_icons/favicon-32x32.png" />
<style type="text/css">
body{ font-family: Arial, Helvetica, sans-serif; color: black; background-color: ivory}
</style>
<title>beelogger</title>
</head>
<body>
<?php
  echo"<h3>Webseite&nbsp;&nbsp;".$_SERVER['SERVER_NAME']."&nbsp;&nbsp;bitte mit https://aufrufen<BR></h3>"."\n";
  $link="https://$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]";
  echo '<h4><a href="'.$link.'" >'.$link.'</a></h4>'."\n";
  echo '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="'.$link.'"target="_blank"><img src="./../beelogger_icons/show.png" height="50px"></a>'."\n";
?>
</body>
</html>
<?php
  exit;
  }
}


error_reporting(0);
if($show_version){
 error_reporting(E_ERROR | E_WARNING | E_PARSE);
 if($show_version==2){error_reporting(E_ALL);ini_set('display_errors', "1");ini_set('display_startup_errors', true);}
}
if(file_exists("beelogger.ini")){rename("beelogger.ini","beelogger_ini.php");unlink("beelogger.ini");}

//var_dump(($_POST));

$beelogger1_List="aktiviert";//init
$Sprache="1";//INIT falls noch keine Speicherung stattfand
if(file_exists("../general_ini.php"))include("../general_ini.php");//Sprache abfragen
if($Sprache=="")$Sprache="1";//INIT
if(file_exists("../beelogger_sprachfiles/Show_Sprache_".$Sprache.".php"))include("../beelogger_sprachfiles/Show_Sprache_".$Sprache.".php");//Sprache einbinden
$bhome=0;
if(file_exists("home.php"))include("home.php");

// eigen-utc-2: Zeitzone aus beelogger_zeitzone.php (Vorgabe Europe/Berlin)
$Zeitzone='Europe/Berlin';
if(file_exists('../beelogger_zeitzone.php'))include('../beelogger_zeitzone.php');
if(!in_array($Zeitzone,timezone_identifiers_list()))$Zeitzone='Europe/Berlin';
date_default_timezone_set($Zeitzone);


$ForscherDateiName=basename(__DIR__).".csv";//Datei löschen
if(file_exists($ForscherDateiName))unlink($ForscherDateiName);

$beelogger=substr(dirname(__FILE__), strrpos(dirname(__FILE__),"/")+1);
if(strchr($beelogger,"\\")){
  $beelogger=substr(dirname(__FILE__), strrpos(dirname(__FILE__),"\\")+1);
}

//Init some vars
$Message="";

$MultiType=1;//anzahl der Waagen pro beelogger
$MultiTypeAnzahl=1;//Anzahl unterbeelogger
$MultiTypeName="";//Duo, Triple ...
$MultiSign="";//D,T,Q...
$Sensor_max_count=13;//anzahl Sensoren pro Waage
$WechselIniName="";//INIT
$WechselMapName="";//INIT

if(strlen($beelogger)< 12 && strpos($beelogger,"beelogger")!==FALSE){
  $ServerMultiNumber=intval(str_replace("beelogger","", $beelogger));
}elseif(strpos($beelogger,'Duo')===0){//Duo an Position1
  $MultiTypeName="Duo";
  $MultiSign="D";
  $ServerMultiNumber=intval(str_replace("Duo","", $beelogger));
  $MultiType=2;//anzahl der Waagen pro beelogger
  $Sensor_max_count=18;
}elseif(strpos($beelogger,'Triple')===0){
  $MultiTypeName="Triple";
  $MultiSign="T";
  $ServerMultiNumber=intval(str_replace("Triple","", $beelogger));
  $MultiType=3;
  $Sensor_max_count=22;
}elseif(strpos($beelogger,'Quad')===0){
  $MultiTypeName="Quad";
  $MultiSign="Q";
  $ServerMultiNumber=intval(str_replace("Quad","", $beelogger));
  $MultiType=4;
  $Sensor_max_count=26;
}elseif(strpos($beelogger,'Penta')===0){
  $MultiTypeName="Penta";
  $MultiSign="P";
  $ServerMultiNumber=intval(str_replace("Penta","", $beelogger));
  $MultiType=5;
  $Sensor_max_count=30;
}elseif(strpos($beelogger,'Hexa')===0){
  $MultiTypeName="Hexa";
  $MultiSign="H";
  $ServerMultiNumber=intval(str_replace("Hexa","", $beelogger));
  $MultiType=6;
  $Sensor_max_count=34;
}
else{
  $MultiType=0;//Unterordner der Multis
  if(strpos($beelogger,'Xanalyse')===0){
    $MultiType=-1;
    $Sensor_max_count=20;
    $XanalyseNummer=intval(substr($beelogger, -1));
  }
  $MultiSign=substr(str_replace("beelogger","",$beelogger),0,1);//D,T,Q,P oder S
  $ServerMultiNumber=substr(preg_replace('![^0-9_]!','',$beelogger),0,-2);
  $ServerMultiUnterordnerNummer=intval(substr($beelogger,-1,1));
  switch($MultiSign){
  case 'D':
    $MultiTypeName="Duo";
    $MultiTypeAnzahl=2;
    break;
  case 'T':
    $MultiTypeName="Triple";
    $MultiTypeAnzahl=3;
    break;
  case 'Q':
    $MultiTypeName="Quad";
    $MultiTypeAnzahl=4;
    break;
  case 'P':
    $MultiTypeName="Penta";
    $MultiTypeAnzahl=5;
    break;
  case 'H':
    $MultiTypeName="Hexa";
    $MultiTypeAnzahl=6;
    break;
  }
  if($MultiTypeAnzahl > 1){
  $WechselIniName="../".$MultiTypeName.$ServerMultiNumber."/beelogger_ini.php";
  $WechselMapName="../".$MultiTypeName.$ServerMultiNumber."/beelogger_map.php";
  $WechselWetterName="../".$MultiTypeName.$ServerMultiNumber."/wetter_daten.php";
  $WechselLocName="../".$MultiTypeName.$ServerMultiNumber."/loc.php";
  }
}

//Init vars not in older beelogger_ini
$KoeKaefig="";
$BeutenLeergewicht="";
$TwoGrid="false";
$chartMobile=3;
$Zoom="0";
$Summe="false";
$Underlay="7";
$Underlay_Mo="6";
$Underlay_Ab="18";
$Underlay_Col="FFFFA4";
$GTS_color="true";
$TageswertAchse="";//Abwärtskomp
$mW_one_y=0;
$FillGraph=array();for($a=0;$a<$Sensor_max_count;$a++){$FillGraph[$a]="";}//needed for config


//POST-Variablen Anmerkungen
if(isset($_POST['termin']))$Termin=$_POST['termin'];
if(isset($_POST['sensor']))$Sensor=$_POST['sensor'];
if(isset($_POST['kurztext'])){
  $Ktext=str_replace('"',"'",$_POST['kurztext']);
  $Ktext=htmlentities(strip_tags(stripslashes($Ktext)));
  $Kurztext=str_replace(",",".",$Ktext);
}
if(isset($_POST['note_icon']))$Note_icon=$_POST['note_icon'];
if(isset($_POST['langtext'])){
  $Ltext=str_replace('"',"'",$_POST['langtext']);
  $Ltext=htmlentities(strip_tags(stripslashes($Ltext)));
  $Langtext=str_replace(',', ";", $Ltext);
}
$Erzeugen="0";if(isset($_POST['erzeugen']))$Erzeugen=$_POST['erzeugen'];
$Loeschen="0";if(isset($_POST['loeschen']))$Loeschen=$_POST['loeschen'];
$Aendern="0";if(isset($_POST['aendern']))$Aendern=$_POST['aendern'];
$Speichern="0";if(isset($_POST['speichern']))$Speichern=$_POST['speichern'];
$Wertloeschen="0";if(isset($_POST['wertloeschen']))$Wertloeschen=$_POST['wertloeschen'];
$NeuWert="0";if(isset($_POST['neuwert']))$NeuWert=htmlentities(strip_tags(stripslashes($_POST['neuwert'])));

//POST-Variablen Passwort
$Passwort="";
if(isset($_POST["passwort"]))$Passwort=htmlentities(strip_tags(stripslashes($_POST['passwort'])));
if($Passwort==""){ if(isset($_SESSION["Spasswort"]))$Passwort=$_SESSION["Spasswort"];}
$_SESSION["Spasswort"]=$Passwort;

$Csvdatei="";//aus browerzeile oder beelogger_ini
if(isset($_GET["csvdatei"]))$Csvdatei=htmlentities(strip_tags(stripslashes($_GET["csvdatei"])));
if($Csvdatei==""){if(isset($_POST["csvdatei"]))$Csvdatei=htmlentities(strip_tags(stripslashes($_POST['csvdatei'])));}

//###################################### config
#//POST-Variablen  beelogger_config.php
$Config="0";
$Csvdownload="0";
$ConfigSichern="0";
if(isset($_POST['config']))$Config=$_POST['config'];

if(isset($_POST['csvdownload']))$Csvdownload=$_POST['csvdownload'];
if($Csvdownload=="1")$ConfigSichern="1";

if(isset($_POST['configsichern']))$ConfigSichern=$_POST['configsichern'];
if($Config=="1")$ConfigSichern="1";

if(!isset($_POST['cfg_complete']))$ConfigSichern="0";

if(!file_exists("beelogger_ini.php")OR(file_exists("pw.php"))OR($ConfigSichern=="1")){
      include("beelogger_config.php");
}
$ConfigSichern="0";
//###################################### config

unset($POST);
$_POST=array();//clear $_POST data

$IconBezeichner=array(
array("1","n_1 Leerrahmen hinzu.png","1 empty frame added","1 Cadre vide ajouté"),
array("2","n_1 Rahmen mit Mittelwand hinzu.png","1 frame with partition board added","1 Cadre avec partition ajouté"),
array("3","n_2 Leerrahmen hinzu.png","2 empty frames added","2 Cadres vides ajoutés"),
array("4","n_2 Rahmen mit Mittelwand hinzu.png","2 frames with partition board added","2 Cadres avec partition ajoutés "),
array("5","n_Absperrgitter.png","Separation grid","Grille de séparation"),
array("6","n_Akkutausch.png","Battery exchange","Changement de batterie"),
array("7","n_Ameisensaeurebehandlung.png","Formic acid treatment","Traitement à l'acide formique"),
array("8","n_Bienenflucht eingesetzt.png","Swarming started","Début d'essaimage"),
array("9","n_Brutwabe entnommen.png","Brood comb removed","Cadre couvain retiré"),
array("10","n_Brutwabe hinzu.png","Brood-comb added","Cadre couvain ajouté"),
array("11","n_Durchsicht - Achtung.png","Inspection - Be careful!","Inspection - Attention!"),
array("12","n_Durchsicht - Alles OK.png","Inspection - All right!","Inspection - OK"),
array("13","n_Durchsicht.png","Inspection","Inspection"),
array("14","n_Fuetterung.png","Feeding","Alimentation"),
array("15","n_Futterwabe entnommen.png","Honeycomb removed","Cadre de miel enlevé"),
array("16","n_Futterwabe hinzu.png","Honeycomb added","Cadre de miel ajouté"),
array("17","n_Futterzarge.png","Feeder","Nourisseur"),
array("18","n_Honigernte.png","Honey harvesting","Récolte de miel"),
array("19","n_Honigraum entfernt.png","Honey top box removed","Rehausse retirée"),
array("20","n_Honigraum hinzu.png","Honey top box added","Rehausse ajoutée"),
array("21","n_Koenigin blau gezeichnet.png","Queen color-coded in blue","Reine marquée en bleu"),
array("22","n_Koenigin gelb gezeichnet.png","Queen color-coded in yellow","Reine marquée en jaune"),
array("23","n_Koenigin gruen gezeichnet.png","Queen color-coded in green","Reine marquée en vert"),
array("24","n_Koenigin rot gezeichnet.png","Queen color-coded in red","Reine marquée en rouge"),
array("25","n_Koenigin weiss gezeichnet.png","Queen color-coded in white","Reine marquée en blanc"),
array("26","n_Oxalsaeurebehandlung.png","Oxalic acid treatment","Traitement àl'acide oxalique"),
array("27","n_Schwarmabgang.png","Swarm departure","Essaimage"),
array("28","n_Totale Brutentnahme.png","Total brood removal","Enlèvement total du couvain"),
array("29","n_Triggeralarm.png","Trigger alarm","Alarme personnalisée"),
array("30","n_Varroabehandlung.png","Varroa treatment","Traitment varroas"),
array("31","n_Varroaeinschub.png","Varroa bottom board","Tiroir à varroas"),
array("32","n_Wetter (Schnee-Hagel-Wind).png","Weather (snow-hail-wind)","Météo (neige-grèle-vent)"),
array("33","n_Bluete.png","Blooming","Floraison"),
);


include("beelogger_ini.php");//Werte neu einlesen
if(file_exists("../general_ini.php"))include("../general_ini.php");//Sprache festlegen
if(($Sprache !="1")&&($Sprache !="2")&&($Sprache !="3"))$Sprache="2";//INIT
if(file_exists("../beelogger_sprachfiles/Show_Sprache_".$Sprache.".php"))include("../beelogger_sprachfiles/Show_Sprache_".$Sprache.".php");//Sprache einbinden

if(!isset($UseIcon)){//compatibility
$UseIcon=array('false','false','false','false','false','true','true','true','true','false','false','false','false');
};
//Schwarmalarm einlesen
$SchwarmAlarmMessageArray=array("-","-","-","-","-","-","-","-");//INIT
if(file_exists('Schwarminfo.php')){
  include('Schwarminfo.php');
  $SchwarmAlarmMessageArray[0]=$SchwarmAlarmMessage;
}

if($MultiType > 1){
  for($is=1;$is <=$MultiType;$is++){
    $WarnFile='../beelogger'.$MultiSign.$ServerMultiNumber."_".$is.'/Schwarminfo.php';
    if(file_exists($WarnFile)){
      include($WarnFile);
      $SchwarmAlarmMessageArray[$is]=$SchwarmAlarmMessage;
    }
  }
}

$AnzahlSensoren=(sizeof($Sensoren)/5);//Eventuell neue Anzahl an Sensoren
$HelpArraySensoren=$Sensoren;
$HelpAnzahlSensoren=$AnzahlSensoren;

if($Csvdatei=='')$Csvdatei=$StandardCSV;//Standard, wenn bisher nichts definiert wurde
if(!file_exists($Csvdatei))$Csvdatei="beelogger.csv";//falls der Standard nicht existiert

if($MultiType==-1){//Xanalyse berechnen
  $AnzahlBeeloggerDateien=sizeof($XanalyseArray);
  $NewCount=0;//INIT
  $NewArray=array();
  $n_array=array();
  for($Xana=0;$Xana <=$AnzahlBeeloggerDateien;$Xana++){
   array_push($n_array,"");//create Array
  }
  array_push($NewArray,$n_array);

  for($Xana=0;$Xana < $AnzahlBeeloggerDateien;$Xana++){
  if($XanalyseArray[$Xana] !=""){//is configured?
    if(strchr($XanalyseArray[$Xana],"\\")){//windows
    $Xanalysebeelogger=substr($XanalyseArray[$Xana],0,-(strlen($XanalyseArray[$Xana])-strpos($XanalyseArray[$Xana],"\\")));
    $XanalyseSensor=substr($XanalyseArray[$Xana],(1+strrpos($XanalyseArray[$Xana],"\\")));
    }else{
    $Xanalysebeelogger=substr($XanalyseArray[$Xana],0,-(strlen($XanalyseArray[$Xana])-strpos($XanalyseArray[$Xana],"/")));
    $xa_s=1 + strrpos($XanalyseArray[$Xana],"/");
    $xa_s=substr($XanalyseArray[$Xana],$xa_s);
    $XanalyseSensor=1+(int)$xa_s;
    }
    $datei="../".$Xanalysebeelogger."/".$Csvdatei;
    if(file_exists($datei)){
     $DateiArray=file($datei);
     $DateiArraySize=sizeof($DateiArray);//Grösse des Arrays

     $i=$DateiArraySize;
     if($i >0){
      while($i--){
        $what=trim($DateiArray[$i]);
        $x=explode(",", $what);
        $s=sizeof($x);//hier wird die Anzahl von Spalten pro Zeile im beelogger.csv ermittelt
        if($x[$s-1] !='')break;
      }
     }
     $NewArray[$NewCount][0]=intdiv((int)$x[$s-1],3600)*3600;//eigen-utc-1: volle Stunde als Zeitstempel
     $NewArray[$NewCount][1+$Xana]=$x[$XanalyseSensor];//Sensordaten
     $NewCount++;
     array_push($NewArray,$n_array);
     for($ix=0;$ix < $i;$ix++){//alle Werte der Datei durchgehen
      $what=trim($DateiArray[$ix]);
      $x=explode(",", $what);
      $s=sizeof($x);
      if(intdiv((int)$x[$s-1],3600)*3600!=$NewArray[$NewCount-1][0]){//Neue Stunde angebrochen (eigen-utc-1)
        array_push($NewArray,$n_array);
        $NewArray[$NewCount][0]=intdiv((int)$x[$s-1],3600)*3600;//eigen-utc-1: volle Stunde als Zeitstempel
        $NewArray[$NewCount][1+$Xana]=$x[$XanalyseSensor];//Sensordaten
        $NewCount++;
      }
     }
    }
  }
 }

 if(sizeof($NewArray)> 5){//sort and save
  $Lastvalue="";
  $LastArrayCount=0;
  asort($NewArray);//eigen-utc-1: sortiert jetzt nach Zeitstempel (Zahl)
  $LastArray=array();
  foreach($NewArray as $value){
    if($value[0] !=$Lastvalue){
      array_push($LastArray,$n_array);
      $LastArrayCount++;
      $LastArray[$LastArrayCount][0]=$value[0];
      for($z=1;$z < $Xana;$z++){
        $LastArray[$LastArrayCount][$z]=$value[$z];
      }
      $Lastvalue=$value[0];
    }else{
      for($z=1;$z < $Xana;$z++){
        if(strlen($value[$z])> 0)$LastArray[$LastArrayCount][$z]=$value[$z];
      }
    }
  }
  $LastArray[0]=$LastArray[1];
  $Message=$SAs[63];
 }
 else{//just some data
  $LastArray=array([strtotime("2022-03-04 05:00"),"18.10","","","",""],[strtotime("2022-03-04 06:00"),"18.60","","","",""]);//eigen-utc-1
  $Message=$SAs[148];
 }

  $aktion=fopen($Csvdatei,"w");
  foreach($LastArray as $val){//make csv-string
  $Output=date("Y/m/d H",(int)$val[0]).":00,";//eigen-utc-1: Anzeige aus dem Zeitstempel
  for($iV=1;$iV <($Xana);$iV++){
    $Output .=$val[$iV].",";
  }
  $Output .=",,,".(int)$val[0]."\r\n";//eigen-utc-1: Zeitstempel direkt, nicht aus dem Text
  fputs($aktion,$Output);
  }
  fclose($aktion);
  if($Csvdatei=="beelogger.csv")CSVbuilder(0);
}//MultiType -1
else{
  CSVbuilder(1);
}

if(!file_exists($Csvdatei)){//no csv?
 foreach(glob("*.csv")as $filename){
  if(str_contains($filename,"notes"))continue;
  if(file_exists($filename)){
    $Csvdatei=$filename;
  break;
  }
 }
}
if(file_exists($Csvdatei)){//Letzte Werte aus .csv auslesen
  $array=file($Csvdatei);
  if(sizeof($array)>0){
  $ErsteZeile=trim($array[0]);
  $x=explode(",", $ErsteZeile);
  $CsvSpaltenAnzahl=sizeof($x);
  $ErstesDatum=$x[$CsvSpaltenAnzahl-1];
  if($CsvSpaltenAnzahl==0)$CsvSpaltenAnzahl=$AnzahlSensoren+4;//falls keine Daten
  $HelpAnzahlSensoren=$AnzahlSensoren;
  $HelpArraySensoren=$Sensoren;
  if($x[$CsvSpaltenAnzahl-2]=="" AND $x[$CsvSpaltenAnzahl-3]=="")$Abzug=4;//neue Datei
  else $Abzug=2;//alte Datei ohne 2 Leerstellen vorm Datum
  if($AnzahlSensoren <($CsvSpaltenAnzahl-$Abzug)){
    for($i=$AnzahlSensoren;$i <=($CsvSpaltenAnzahl-($Abzug+1));$i++){//es werden Quasi-Sensoren erzeugt
      $HelpArraySensoren[$i*5]=$i+1;
      $HelpArraySensoren[$i*5+1]="black";
      $HelpArraySensoren[$i*5+2]="false";
      $HelpArraySensoren[$i*5+3]="'y'";
      $HelpArraySensoren[$i*5+4]="[ ]";
      array_push($UseIcon);$UseIcon[$i]="false";
    }
    $HelpAnzahlSensoren=(sizeof($HelpArraySensoren)/5);
  }
  }//array size
}//ifcsv-file_exists..
?>

<!DOCTYPE html>
<html lang="de">
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<script type="text/javascript" src="../dygraph.js" charset="UTF-8"></script>
<link rel="stylesheet" href="../dygraph_beelogger.css">
<link rel="shortcut icon" href="../beelogger_icons/favicon-32x32.png" />
<style type="text/css">
body{ font-family: Arial, Helvetica, sans-serif; color: black; background-color: ivory}

textarea{ font-size: 14px; }
#Titelbox{
  background-color:transparent;
  position:relative;
  top:0px;
  left:10px;
  font-size: 32px;
  width:95%;
  -moz-text-size-adjust: none;
}
#Auswahlbuttons{
  background-color:transparent;
  position:relative;
  top:0px;
  left:10px;
  font-size: 14px;
  width:95%;
  -moz-text-size-adjust: none;
}
#Message_box{
  background-color:transparent;
  position:relative;
  top:7px;
  left:10px;
  width:95%;
  padding:5px;
  background:#ffff;
  border:1px solid black;
  border-radius:5px;
  font-family:Arial,'Times New Roman',serif;
  font-size: 14px;
  -moz-text-size-adjust: none;
}
#DatenArea{
  background-color:white !important;
  position:relative;
  top:-48px;
  left:15px;
  width:95%;
  z-index:1;
  -moz-text-size-adjust: none;
}
#DatenAreaAnmerkAend{
  background-color:white !important;
  position:relative;
  top:-48px;
  left:15px;
  width:95%;
  z-index:1;
  -moz-text-size-adjust: none;
}
#DatenAreaLoeschWert{
  background-color:white !important;
  position:relative;
  top:-48px;
  left:15px;
  width:95%;
  z-index:1;
  -moz-text-size-adjust: none;
}
#DatenAreaKonfig{
  background-color:white !important;
  position:relative;
  top:-48px;
  left:15px;
  width:95%;
  z-index:1;
  -moz-text-size-adjust: none;
}
#DatenAreaAendAnmrk{
  background-color:white !important;
  position:relative;
  top:-48px;
  left:15px;
  width:95%;
  z-index:1;
  -moz-text-size-adjust: none;
}
#Sensorbuttons{
background-color:transparent;
position:relative;
top:5px;
left:5px;
height:30px;
width:95%;
font-size:14px;
display:-webkit-flex; /* Safari */
-webkit-flex-wrap: wrap; /* Safari 6.1+ */
display:flex;
flex-wrap:wrap;
}

<?php
//SetButtons
for($s=0;$s < $HelpAnzahlSensoren;$s++){
 if($UseIcon[$s]=="true"){
  echo"\n".'#cbl'.$s.'{
  display: inline-block; margin: 10px; margin-bottom:-10px; margin-left:10px;
  background-image: url("../beelogger_icons/off_'.$Icon[$s].'");
  background-repeat:no-repeat;
  opacity:0.5;
  width:38px;
  border-bottom:1px solid '.$HelpArraySensoren[$s*5+1].';
  height:30px;';
  if(is_numeric($HelpArraySensoren[$s*5]))echo"display:none;";//Buttons die als Name nur Zahl haben
  echo'}'."\n";
  echo'#cb'.$s.':checked + #cbl'.$s.'{
     background-image: url("../beelogger_icons/off_'.$Icon[$s].'");
     opacity:1;
     height:30px;
     border-bottom:7px solid '.$HelpArraySensoren[$s*5+1].';';
   if(is_numeric($HelpArraySensoren[$s*5]))echo"display:none;";//Buttons die als Name nur Zahl haben
   echo'}'."\n";
   echo'#cb'.$s.'{display:none;}';
 }//if($UseIcon[$s]=="true")
 else{
  $SchriftWeite=round(9.3 * strlen($HelpArraySensoren[$s*5]));
  if(strlen($HelpArraySensoren[$s*5])< 5)$SchriftWeite +=10;//Kurze Namen brauchen etwas größere Buttons

//Sensor Buttons
  echo"\n#ck-button".$s."{
  position:relative;top:10px;left:5px;
  height:22px;margin:6px;background-color:#EFEFEF;
  overflow:hidden;float:left;
  -webkit-transition-duration:400ms; /* Safari */
  transition-duration:400ms;";

  if(($HelpArraySensoren[$s*5]=="Gewicht")and $bhome > 0)echo"display:none;";
  if(is_numeric($HelpArraySensoren[$s*5]))echo"display:none;";//Buttons die als Name nur Zahl haben
  echo"\n  border-radius:15px;border:1px solid ".$HelpArraySensoren[$s*5+1].";";
  echo"\n}\n";

  echo"#ck-button".$s." input:not(:checked)+ :hover{
    background-color:lightgrey;
    color:".$HelpArraySensoren[$s*5+1].";
}\n";
echo"#ck-button".$s." input:checked + :hover{
    background-color:".$HelpArraySensoren[$s*5+1].";
    color:lightgrey;
}\n";
echo"#ck-button".$s." label{
    color:".$HelpArraySensoren[$s*5+1].";
    float:left;
    width:".$SchriftWeite."px;
}
#ck-button".$s." label span{
    text-align:center;
    padding:3px 0px;
    display:block;
}
#ck-button".$s." label input{
    position:absolute;
    top:-20px;
}
#ck-button".$s." input:checked + span{
    background-color:".$HelpArraySensoren[$s*5+1].";
    color:white;
}";
 }//else
}//for($s=0;$s < $HelpAnzahlSensoren;$s++)

//Button Tageswerte
echo"
#ck-button".$s."{
position:relative;top:10px;left:5px;
height:22px;margin:6px;background-color:#EFEFEF;
overflow:hidden;float:left;
-webkit-transition-duration:400ms; /* Safari */
transition-duration:400ms;border-radius:4px;
border:1px solid #000000;";
 if(($MultiType==-1)OR($bhome > 0))echo"\ndisplay:none;";//TW
echo"}";
echo"
#ck-button".$s." input:not(:checked)+ :hover{
  background-color:grey;
  color:black;
}";
echo"
#ck-button".$s." input:checked + :hover{
  background-color:grey;
  color:white;
}";

$SchriftWeite=round(9.1 * strlen($SAs[64]));
echo"
#ck-button".$s." label{
  color:black;
  float:left;
  width:".$SchriftWeite."px;
}
#ck-button".$s." label span{
  text-align:center;
  padding:3px 0px;
  display:block;
}
#ck-button".$s." label input{
  position:absolute;
  top:-20px;
}
#ck-button".$s." input:checked + span{
  background-color:black;
  color:#fff;";
echo"}";

echo'
 #Nummer_Box{
  background-color:transparent;
  position:relative;
  top:16px;
  left:6px;';
//if(($MultiType==-1)OR($MultiType > 1)OR($bhome > 0))echo"\ndisplay:none;";
 if(($MultiType==-1)OR($bhome > 0))echo"\ndisplay:none;";//TW
echo'}';

echo'
 #sum_grenze{
  background-color:transparent;
  position:relative;
  top:18px;
  left:5px;';
  if(($MultiType==-1)OR($MultiType > 1)OR($bhome > 0))echo"\ndisplay:none;";
  echo'}';

$s++;
//Button Summe
echo"
#ck-button".$s."{
position:relative;top:10px;left:5px;
height:22px;margin:6px;background-color:#EFEFEF;
overflow:hidden;float:left;
-webkit-transition-duration:400ms; /* Safari */
transition-duration:400ms;border-radius:4px;
border:1px solid orange;";
if(($MultiType==-1)OR($bhome > 0))echo"\ndisplay:none;";
echo"}";

echo"
#ck-button".$s." input:not(:checked)+ :hover{
  background-color:#FFC31E;/*lightorange;*/
  color:grey;
}";
echo"
#ck-button".$s." input:checked + :hover{
  background:#FFC31E;/*lightorange;*/
  color:grey;
}";
echo"
#ck-button".$s." label{
  color:orange;
  float:left;
  width:58px;
}
#ck-button".$s." label span{
  text-align:center;
  padding:3px 0px;
  display:block;
}
#ck-button".$s." label input{
  position:absolute;
  top:-20px;
}
#ck-button".$s." input:checked + span{
  background-color:orange;
  color:#fff;";
echo"}";


if($BeutenLeergewicht !="")if(((int)$BeutenLeergewicht)>0){
echo"
#ck-button99{
position:relative;top:10px;left:5px;
height:21px;margin:6px;background-color:WHITE;
overflow:hidden;float:left;
-webkit-transition-duration:400ms; /* Safari */
transition-duration:400ms;border-radius:15px;
z-index:-1;border-radius:4px;border:1px solid grey;}

#ck-button99 label{
  color:grey;
  float:left;";
  $SchriftWeite=round(11 * strlen($SAs[67]));
  if((int)$Honigraeume[0] < 1 AND(int)$Honigraeume[2] < 1 AND(int)$BeutenUtils[0][0] < 1 AND(int)$BeutenUtils[1][0] < 1 AND(int)$BeutenUtils[2][0] < 1)echo"  width:".($SchriftWeite+50)."px;";
  else echo"  width:".($SchriftWeite+115+(((int)$Honigraeume[0]+(int)$Honigraeume[2]+(int)$BeutenUtils[0][0]+(int)$BeutenUtils[1][0]+(int)$BeutenUtils[2][0])*20))."px;";
echo" }";

echo"
#ck-button99 label span{
  text-align:center;
  padding:2px 0px;
  display:block;
}
#ck-button99 label input{
  position:absolute;
  top:-20px;
}
#ck-button99 input:checked + span{
  background-color:white;
  color:#fff;
}";
}

//Dummybutton für Abstand
echo"
#ck-button999{
position:relative;top:10px;left:5px;
height:21px;margin:6px;background-color:WHITE;
overflow:hidden;float:left;
-webkit-transition-duration: 400ms; /* Safari */
transition-duration: 400ms;
z-index:-1;border-radius:2px;border:0px solid grey;}

#ck-button999 label{
  color:grey;
  float:left;
  width:1px;
}
#ck-button999 label span{
  text-align: center;
  padding:0px 0px;
  display:none;
}
#ck-button999 label input{
  position:absolute;
  top:-20px;
}
#ck-button999 input:checked + span{
  background-color: white;
  color:#fff;
}";
?>

#AlleAuswahlbutton{
  position:relative;
  top:10px;
  left:5px;
  height:22px;
  margin:6px;
  background-color:#EFEFEF;
  border-radius:4px;
  border:1px solid #D0D0D0;
  overflow:auto;
  float:left;
}
#AlleAuswahlbutton :hover{background:#fff;}
#AlleAuswahlbutton label{color:black;float:left;width:100%;}
#AlleAuswahlbutton label span{text-align:center;padding:2px 0px;display:block;}
#AlleAuswahlbutton label input{text-align:center; position:absolute;top:-20px;}

#trenner{
  position:relative;
  top:5px;
  left:0px;
  height:1px;
  width:95%;
  background-color: ivory
  z-index:-1;
}

#NavigationAnzeige{
  background-color:transparent;
  position:relative;
  top:17px;
  left:4px;
  height:21px;
  display:flex;
  flex-wrap:wrap;
  display:-webkit-flex; /* Safari */
  -webkit-flex-wrap: wrap; /* Safari 6.1+ */
  -moz-text-size-adjust: none;
}
#KonfigAnzeige{
  position:relative;
  background-color:white !important;
  top:-55px;
  left:10px;
}
#BL_grafik{
  position:relative;
  top:20px;
  left:10px;
}
#BL_grafik .dygraph-ylabel{color:black;}
#BL_grafik .dygraph-axis-label-y1{color:black;}
#BL_grafik .dygraph-y2label{color:black;}
#BL_grafik .dygraph-axis-label-y2{color:black;}
</style>
<title>beelogger.de - Datenlogger für Imker</title>
</head>

<?php
//Ermittlung $Bienenvolkbezeichnung
if($Bienenvolkbezeichnung=="auto"){//nur wenn oben kein eigener Name angegeben wurde
  $pfad=getcwd();//kompletter Verzeichnispfad
  $verz=strrchr($pfad, "/");//Verzeichnisname einschließlich des / zu Beginn
  $BienenvolkbezeichnungToEcho=str_replace("/","",$verz);// / noch entfernt
}
else $BienenvolkbezeichnungToEcho=html_entity_decode($Bienenvolkbezeichnung);
$BienenvolkbezeichnungToEcho=html_entity_decode($BienenvolkbezeichnungToEcho);

$LetztesVBatt="33";
$LetztesLicht=0;
$LetztesVSolar=0;
$AktualisierungsStamp=0;
$AktualisierungStampMessage=0;
$SendeIntervall=15;

$w_msg=1;//no data
$col_red=0;
if(file_exists('week.csv')){//array füllen mit aktueller csv-datei
  $input='week.csv';
  $array=file($input);
  $i=sizeof($array);
  if($i>1){
   $w_msg=0;
   while($i--){
    $what=trim($array[$i]);
    $x=explode(",", $what);
    $LetzteZeile=$x;//merke Letzte Zeile für beelogger_ini.php-Ansicht
    $s=sizeof($x);//hier wird die Anzahl von Spalten pro Zeile im beelogger.csv ermittelt
    if($x[$s-1] !=''){//um hier die letzte Spalte=Zeitstempel abzufragen
     $AktualisierungsStamp=$x[$s-1];
     $AktualisierungStampMessage=$AktualisierungsStamp;
   if($AktualisierungsStamp <(time()- 86400*2))$col_red=1;
     if(($MultiType==0)OR($MultiType==1)){
      $LetztesLicht=$x[5];//wird gebraucht um das Sendeintervall zu ermitteln
      $LetztesVBatt=$x[7];//wird gebraucht um den Akkuzustand anzuzeigen
      $LetztesVSolar=$x[8];//wird gebraucht um das Sendeintervall zu ermitteln
     }
     elseif($MultiType > 1){
      $LetztesLicht=$x[5];//wird gebraucht um das Sendeintervall zu ermitteln
      $LetztesVBatt=$x[(9+($MultiType-1)*3)];//wird gebraucht um das Sendeintervall zu ermitteln
      $LetztesVSolar=$x[(10+($MultiType-1)*3)];//wird gebraucht um das Sendeintervall zu ermitteln
     }
     $LetztesGewicht=$x[6];
     break;
    }
   }
   $NummerLetzteZeile=$i;
   $ZeitFuerNeueNote=$AktualisierungsStamp;//Hilfe für neue Note bei neuer Zeitintervalleingabe
   $Aktualisierung=date("d.m.Y H:i:s",$AktualisierungsStamp);
  }
}
if($w_msg){//no data
  if($MultiType==-1)$Message=$SAs[148];
  else $Message=$SAs[24];
  $Aktualisierung="-<br>";
}

//NotesDatei erzeugen, falls noch nicht geschehen
if(!file_exists("notes.csv")){$fp=fOpen("notes.csv", "w"); fclose($fp);}
foreach(glob("*.csv")as $csvfile){if(fileperms($csvfile)!=0x0600)chmod($csvfile,0600);}
chmod("week.csv",0604);
sleep(1);

function assignNotesfile($noteAlt){
  global $NotesFileName,$Csvdatei;
  $NotesFileName="notes".$Csvdatei;//notesArchiv
  if($noteAlt)if(!file_exists($NotesFileName))$NotesFileName="notes_old.csv";
  if(!file_exists($NotesFileName))$NotesFileName="notes.csv";
  if(($Csvdatei=="beelogger.csv")OR($Csvdatei=="month.csv")OR($Csvdatei=="week.csv")){
    $NotesFileName="notes.csv";
  }
}

//Formular zum Erzeugen einer neuen Anmerkung wurde abgeschickt -------------------
if($Erzeugen=="1"){
  if($Passwort !=''){
    $Message=$SAs[25]."!<br>";//oder mit falschem Passwort
    if($Passwort==$BeeloggerShowPasswort){//Passwortcheck korrekt - Neue Anmerkung erzeugen
      $SensorNummer=0;
      for($i=0;$i < $AnzahlSensoren;$i++){
    $H_Sens=html_entity_decode($Sensoren[$i*5]).' '.html_entity_decode($Sensoren[$i*5+4]);
        if($Sensor==$H_Sens)$SensorNummer=$i;
      }
      $Termin=substr($Termin, 0, -3);
      $Aktualisierung=date("Y/m/d H:i:s",$Termin);
      if($Kurztext=='')$Kurztext='?';//Falls Felder leer - Event nachträglich in "Anmerkungen" editierbar
      if($Langtext=='')$Langtext=$SAs[26];
      $Langtext=str_replace(",",".", $Langtext);//Kommas müssen raus
      $Kurztext=str_replace(",",".", $Kurztext);//Kommas müssen raus
      $value=$SensorNummer.",".$Aktualisierung.",";

      if($Note_icon !=""){
        $value .=$Note_icon;
        if($Langtext==$SAs[26] OR $Langtext==$SAs[133]){
          if($Sprache=="1")$value .="&".substr(substr($Note_icon,21),0,-4);
          else{
            $i=0;
             while($i < sizeof($IconBezeichner)){
              $Gefunden=false;
              if(substr($Note_icon,19)==$IconBezeichner[$i][1]){
                $value .="&".$IconBezeichner[$i][$Sprache];
                $Gefunden=true;
                break;
              }
              $i++;
             }
            if($Gefunden==false)$value .="&".substr(substr($Note_icon,21),0,-4);
          }
        }
        else $value .="&".html_entity_decode($Langtext);
      }
      else $value .=html_entity_decode($Kurztext)."&".html_entity_decode($Langtext);

      $value .=",".$Termin."\r\n";

      assignNotesfile(0);
      $fp=fOpen($NotesFileName, "a");//Daten zurückschreiben notes.csv öffnen und Wert anfügen oder Datei neu erstellen
      $OK=fputs($fp, $value);
      fclose($fp);
      if($OK > 0)$Message=$SAs[27]."!<br>";
    }//if$ BeeloggerShowPasswort
  }//if$Passwort
}//if$Erzeugen


//Formular zum löschen einer Anmerkung wurde abgeschickt Übergabevariable $Termin=TimeStamp
if($Loeschen=="1"){
 if($Passwort==$BeeloggerShowPasswort){
  assignNotesfile(1);
  $n_array=file($NotesFileName);
  $narray=array();
  $ni=0;

  $Counter=0;
  $fp=fOpen($NotesFileName, "w");
  foreach($n_array as $val){
    $Zeile=trim($val);
    $x=explode(",", $Zeile);
    $ZeilenDatumStamp=$x[sizeof($x)-1];
    if($ZeilenDatumStamp !=$Termin){
      $OK=fputs($fp, $val);
      if($ZeilenDatumStamp > $ErstesDatum){
        $narray[$ni]=$narrayROH[$i];
        $ni++;
      }
    }
    $Counter++;
  }
  fclose($fp);

  if($OK > 0)$Message=$SAs[28]."!<br>";
  if($Counter==1)$Message=$SAs[29]."<br>";//Der Fall, das die letzte Anmerkung gelöscht wurde
 }//if$passwort
 else $Message=$SAs[25]."!";
}//ifloeschen=1



//Formular zum speichern einer veränderten Anmerkung wurde abgesendet Übergabevariable $Termin=Stamp----------
if($Speichern=="1"){
  assignNotesfile(1);
  $narray=file($NotesFileName);
  $ni=sizeof($narray);

  $AltNeuTermin=explode("%",$Termin);
  $AltNeuSensor=explode("%",$Sensor);

//alte Note im narray finden und löschen
  for($a=0;$a < $ni;$a++){
    $what=trim($narray[$a]);
    $x=explode(",", $what);
    $s=sizeof($x);
    if(($x[$s-1]==$AltNeuTermin[0])&&($x[0]==$AltNeuSensor[0]))$narray[$a]='';
  }//for $a

  $r=0;
  for($b=0;$b < $ni;$b++){
    if($narray[$b] !='')$kleinarray[$r]=$narray[$b];
    $r++;
  }//for $b
  $Aktualisierung=date("Y/m/d H:i:s",$AltNeuTermin[1]);
  if($Kurztext=="")$Kurztext="?";
  $Kurztext=str_replace(",",";", $Kurztext);//Kommas müssen raus
  $Langtext=str_replace(",",";", $Langtext);//Kommas müssen raus

  $kleinarray[$r]=$AltNeuSensor[1].",".$Aktualisierung.",";
  if($Note_icon==""){
    $kleinarray[$r]=$kleinarray[$r].html_entity_decode($Kurztext);
    if($Langtext==$SAs[26])$Langtext=substr(substr($Note_icon,2),0,-4);
  }
  else $kleinarray[$r]=$kleinarray[$r].$Note_icon;

  $kleinarray[$r]=$kleinarray[$r]."&".html_entity_decode($Langtext).",".$AltNeuTermin[1]."\r\n";//veränderte Note angehängt
//Daten zurückschreiben
  $fp=fOpen($NotesFileName, "w");
  foreach($kleinarray as $values){ fputs($fp, $values);}
  fclose($fp);
  $Message=$SAs[31]."<br>";

}//ifspeichern=1
//ENDE veränderte Anmerkung speichern


//Formular zum löschen oder Ändern eines DatenWertes Übergabe: $Termin + $Sensor + $NeuWert
if($Wertloeschen=="1"){
if($Passwort !=''){
 $Message=$SAs[25]."!<br>";//oder mit falschem Passwort
 if($Passwort==$BeeloggerShowPasswort){//Passwortcheck korrekt
  $Termin=substr($Termin, 0, -3);//Format kommt mit 3 Stellen zuviel an
  $input="beelogger.csv";//die Mutterdatei wird natürlich bearbeitet
  $array=file($input);

//Stelle des Sensors im Array suchen
  $a=0;
  while($a < $AnzahlSensoren){
    $H_Sens=html_entity_decode($Sensoren[$a*5]).' '.html_entity_decode($Sensoren[$a*5+4]);
    if($H_Sens==$Sensor)break;
    $a++;
  }
  $Wertposition=($a+1);//das Datum steht noch an Stelle 0 in der csv-Datei deshalb um einen erhöhen

//wert im Array suchen....
  $i=sizeof($array);
  while($i--){
    $what=trim($array[$i]);
    $x=explode(",", $what);
    $s=sizeof($x);//hier wird die Anzahl von Spalten pro Zeile im beelogger.csv ermittelt
    if($x[$s-1]==$Termin)break;
  }
  if($i<0)$Message="...sorry!<br>";//oops
  else{
	$value="";
	for($v=0;$v <($s-1);$v++){
		if($v==$Wertposition)$value=$value.$NeuWert.",";//Wert gelöscht oder ersetzt
		else $value=$value.$x[$v].",";
	}
	$value=$value.$x[($s-1)]."\r\n";//letzte Position ohne Komma mit Umbruch
	$array[$i]=$value;//$i Zeile mit dem zu ändernden Wert

	//Daten zurückschreiben
	$filename="beelogger.csv";
	$fp=fOpen($filename, "w");
	foreach($array as $values){$send=fputs($fp,$values);}
	fclose($fp);

	CSVbuilder(0);//month.csv und week.csv erneuern
	if($send > 0)$Message=$SAs[30];
  }
}//if$ Passwort
}//if$Passwort
}//ifWert löschen

echo'<body><div id="Titelbox">';

echo"\n<table width=95%>";
  echo"\n<td>";
  echo"\n<table>";
  echo'<td><style="font-size:50px"><font color=#088A08>';
  echo'&nbsp;<b>'.$BienenvolkbezeichnungToEcho.'&nbsp;</b></style></td>';
  if($show_version)echo"\n".'<td><span style="font-size:12px">&nbsp;&nbsp;'.$Softwareversion.'</span></td>';

  if($KoeAnzeige!='' AND $KoeAnzeige!="deaktiviert"){
    if($KoeKaefig=="aktiviert")$KoeAnzeige=str_replace("zeichnet.png","kaefigt.png",$KoeAnzeige);
    echo"<td><img src='../beelogger_icons/".$KoeAnzeige."' width='30' height='30' style='margin-bottom:-5px'; title='".$KoeInfo."'></td>";
  }
  echo"\n</table>\n</td>";
  echo"\n<td align=right>\n<table><tr><td align=center>";

  $beeloggerMap2="";
  $beeloggerMap2BeeID="";
  $MapStatus=" ";

  if($WechselMapName=="")$MapNameNow="beelogger_map.php";
  else $MapNameNow=$WechselMapName;
  if(file_exists($MapNameNow)){
    include($MapNameNow);
    $MultiMapper=FALSE;
    if($MapNameNow !="beelogger_map.php"){//falls Unterbeelogger eines Multi
      if($beeloggerMapWaage > 0)$MultiMapper=TRUE;
    }
    if($MultiType >=1)$MultiMapper=TRUE;
//MAP2
    if(($beeloggerMap2Status=="[UPDATED]" OR $beeloggerMap2Status=="[CHANGED]")AND $MultiMapper==TRUE){//nochmal gegenchecken
        $ch=curl_init("https://map2.beelogger.de/log.php?mapid=".$beeloggerMap2ID."&beeid=".$beeloggerMap2BeeID."&do=372664");//cURL ínitialisieren
        curl_setopt($ch, CURLOPT_HEADER, 0);//Header soll nicht in Ausgabe enthalten sein
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        $ServerAntwort=curl_exec($ch);//Ausführen
        curl_close($ch);//Objekt schließen und Ressourcen freigeben
        if($ServerAntwort=="[ONLINE]"){
          echo"\n<a href='https://beelogger.de/?page_id=196999' target='_blank'><img src='../beelogger_icons/map_aktiv.png' width='70' height='30' style='margin-bottom:-9px'; title='beeloggerMap: ".$ServerAntwort;
          $MapStatus=$ServerAntwort;
          echo"'></a>";
        }else{
          echo"\n<a href='https://beelogger.de/?page_id=196999' target='_blank'><img src='../beelogger_icons/map_inaktiv.png' width='70' height='30' style='margin-bottom:-9px'; title='beeloggerMap2 ".$SAs[33]."'></a>";
          $MapStatus=$SAs[33];
        }
      }
      elseif($MultiMapper==TRUE OR $beeloggerMap2=="deaktiviert"){
        echo"\n<a href='https://beelogger.de/?page_id=196999' target='_blank'><img src='../beelogger_icons/map_inaktiv.png' width='70' height='30' style='margin-bottom:-9px'; title='beeloggerMap2 ".$SAs[33]."'></a>";
        $MapStatus=$SAs[33];
      }
  }//if(file_exists($MapNameNow))

  echo"</td></tr>";

$TriggerAktiv=false;
if($MultiType > 0){
  if($WechselIniName !="")include($WechselIniName);
  for($i=1;$i<5;$i++){
    if($TriggerAlarmArray[$i][1]=="aktiviert" OR $TriggerAlarmArray[$i][2]=="aktiviert" OR $TriggerAlarmArray[$i][7]=="aktiviert"){
      $TriggerAktiv=true;break;
    }
  }
}

//read notes file
$trigger_in_note=0;
$notes_i=0;
$narray=array();
assignNotesfile(1);
if(file_exists($NotesFileName)){
  $narrayROH=file($NotesFileName);
  for($i=0;$i < sizeof($narrayROH);$i++){
    $AnmerkungZeile=trim($narrayROH[$i]);
    $x=explode(",",$AnmerkungZeile);
    $AnmerkungSpaltenAnzahl=sizeof($x);
    $AnmerkungDatum=$x[$AnmerkungSpaltenAnzahl-1];
    if($AnmerkungDatum > $ErstesDatum){
      array_push($narray,$narrayROH[$i]);
      $notes_i++;
	  if(strstr($narrayROH[$i],"Triggeralarm"))$trigger_in_note=1;//Iconname Triggeralarm
    }
  }
}//iffile exists

if($TriggerAktiv){
   echo'<tr align=center><td>';
   for($i=0;$i < 5;$i++){
    if($TriggerAlarmArray[$i][1]=="aktiviert" OR $TriggerAlarmArray[$i][2]=="aktiviert" OR $TriggerAlarmArray[$i][7]=="aktiviert"){ echo'<img src="../beelogger_icons/n_Triggeralarm.png" title="Triggeralarm'.$i.': '.$Sensoren[(5*$TriggerAlarmArray[$i][3])].' '.$TriggerAlarmArray[$i][4].' '.$TriggerAlarmArray[$i][5].'" height=25 style=';
	if($TriggerAktiv && $trigger_in_note)echo'"margin-top:0px; background-color:orange;">';//trigger in data
	else echo'"margin-top:0px;">';
	}
   }
   echo"</tr>";
}
else echo"\n<td align=center style='font-size:12px'>".$MapStatus."</td>";
echo"\n</table>";

include("beelogger_ini.php");//REINIT

 if(file_exists("beelogger_wetter.php"))include("beelogger_wetter.php");
 echo"\n</td></table>";
 echo"\n</div>";//Titelbox

if(($Config=="0")OR($Passwort !=$BeeloggerShowPasswort)){
//<!------- 3 Auswahlbuttons -------->
echo '<div id="Auswahlbuttons"><b>'.$SAs[35].':&nbsp;</b>';
//Listbox beelogger
 $dir="../";
 $files=scandir($dir);
 natcasesort($files);

//Array angezeigter beelogger neu anordnen - nach Duo Triple(E), Quad(M), Hexa(N), Penta(R)und Sept
  $beeloggerArraySize=0;
  $Passwort_Show_Counter=0;
  $beeloggerArray=array(array());
//index in Array  $ind_Beelogger=0;  $ind_Bienenvolkbezeichnung=1;  $ind_Farbe=2;
  foreach($files as $file){
    if($file !="mobile" && $file !="beelogger_icons" && $file !="beelogger_sprachfiles" && $file !="." && $file !=".." && is_dir("../".$file)){
      $ininame="../".$file."/beelogger_ini.php";
      $showname="../".$file."/beelogger_show.php";
      if(file_exists($ininame))include($ininame);
      if($beelogger1_List=="deaktiviert"){if($file=="beelogger1"){if($file !=basename(realpath('.')))continue;}}
      if($BeeloggerShowPasswort=="Show"){
        $AlertArray[$Passwort_Show_Counter]=$file;//Ordnernamen merken
        ++$Passwort_Show_Counter;//für Alert-Info
      }
      $file=str_replace("T","E",$file);
      $file=str_replace("Q","M",$file);
      $file=str_replace("H","N",$file);
      $file=str_replace("P","R",$file);
      array_push($beeloggerArray);
      $beeloggerArray[$beeloggerArraySize][0]=$file;
      $beeloggerArray[$beeloggerArraySize][1]=strtolower($Bienenvolkbezeichnung);
      if($beeloggerArray[$beeloggerArraySize][1]=="auto")$beeloggerArray[$beeloggerArraySize][1]="zzz";
      $beeloggerArray[$beeloggerArraySize][2]="black";
      $Bienenvolkbezeichnung="zzz";//RESET
      $beeloggerArraySize++;
    }
  }
  if($beeloggerArraySize==0){
    $beeloggerArray[0][0]="beelogger1";
    $beeloggerArray[0][1]="zzz";
    $beeloggerArray[0][2]="black";
    $beeloggerArraySize++;
  }
  $Newfiles=$beeloggerArray;
  for($bb=0;$bb<$beeloggerArraySize;$bb++){
    $f_name=$Newfiles[$bb][0];
    $f_name=str_replace("E","T",$f_name);
    $f_name=str_replace("M","Q",$f_name);
    $f_name=str_replace("N","H",$f_name);
    $f_name=str_replace("R","P",$f_name);
    $beeloggerArray[$bb][0]=$f_name;
  }

//Farben zuordnen
   $GruppenFarben=array("green","blue","orange","olive","deepskyblue","purple","lime","black","yellow","red");
   $FarbCounter=0;
   $MultiArray=array('Duo','Triple','Quad','Hexa','Penta','Sept');
    foreach($MultiArray as $EachMulti){
      for($i=0;$i<$beeloggerArraySize;$i++){
        if(strpos($beeloggerArray[$i][0],$EachMulti)!==FALSE){
          $EachMultiNumber=intval(str_replace($EachMulti,"",$beeloggerArray[$i][0]));
          $beeloggerArray[$i][2]=$GruppenFarben[$FarbCounter];
          for($j=0;$j < $beeloggerArraySize;$j++){
            if(strpos($beeloggerArray[$j][0],(substr($EachMulti,0,1).$EachMultiNumber))!==FALSE){
              $beeloggerArray[$j][2]=$GruppenFarben[$FarbCounter];
              }
            }
          $FarbCounter++;
          }
        }
      }
//Ende Farben Zuordnen

if($beeloggerNamenSortierung=="aktiviert"){//Info in general_ini
  foreach($beeloggerArray as $nr=> $inhalt){
    $ABienenvolkbezeichnung[$nr]=strtolower($inhalt[1]);
  }
  array_multisort($ABienenvolkbezeichnung, SORT_NATURAL, $beeloggerArray);
}

echo"<select name='beelogger' onChange='document.location.href=this.value'".' title="'.$SAs[34].'">';
echo"\n";

for($i=0;$i < $beeloggerArraySize;$i++){
  $filename="../".$beeloggerArray[$i][0]."/beelogger_show.php";
  if(file_exists($filename)){
    $ininame="../".$beeloggerArray[$i][0]."/beelogger_ini.php";
    $csvname="../".$beeloggerArray[$i][0]."/beelogger.csv";
    if($beeloggerArray[$i][0]==basename(realpath('.')))echo'<option style="color:'.$beeloggerArray[$i][2].';" value='.$filename." selected>";
    else{
      if(file_exists($ininame)AND file_exists($csvname))echo'<option style="color:'.$beeloggerArray[$i][2].';" value='.$filename.">";
      else echo'<option style="color:gray;" value='.$filename.">";
    }
    $ShowFileName=str_replace("beelogger", "", $beeloggerArray[$i][0]);
    $Bienenvolkbezeichnung="auto";//INIT
    if(file_exists($ininame))include($ininame);
    if($beeloggerNamenSortierung=="aktiviert"){
      if($Bienenvolkbezeichnung !="auto")echo html_entity_decode($Bienenvolkbezeichnung)." (".$ShowFileName.")";
      else echo $beeloggerArray[$i][0];
    echo"</option>"."\n";
    }
    else{
      if($Bienenvolkbezeichnung !="auto")echo $ShowFileName." (".html_entity_decode($Bienenvolkbezeichnung).")";
      else echo $beeloggerArray[$i][0];
      echo"</option>"."\n";
    }
  }//if(file_exists($filename))
}

echo"</select>"."\n";

$MerkeDassButtonDisabled=false;
$RollPeriod="1";//Default
$TageswertAnzeige='false';//Default
$AkkuLeerSchwelle=0;//RESET
$AkkuVollSchwelle=0;//RESET
$IntervallSendeSteuerung="";//RESET
include("beelogger_ini.php");//passende Werte zur Show wieder initialisieren

if($MultiType > 1){
  echo"&nbsp;&nbsp;";
  echo'<input type="button" value="'.$MultiTypeName.' '.$ServerMultiNumber.'" style="background-color:#a9dfbf;" onclick="window.location.href=';
  echo "'../".$MultiTypeName.$ServerMultiNumber."/beelogger_show.php'".'"/>&nbsp;&nbsp;';
  for($i=1;$i <=$MultiType;$i++){
    echo'<a href="../beelogger'.$MultiSign.$ServerMultiNumber.'_'.$i.'/beelogger_show.php"><input type="button" style="background-color:hsl(360,0%,'.(100-$i*10).'%);" value="'.$MultiSign.$ServerMultiNumber."- ".$i.'" onclick="window.location.href=';
    echo"'../beelogger".$MultiSign.$ServerMultiNumber."_".$i."/beelogger_show.php'".'"/></a>&nbsp;&nbsp;'."\n";
  }
}
if($MultiType==1){
  echo"&nbsp;&nbsp;";
  echo'<input type="button" value=" beel. '.$ServerMultiNumber.' " style="background-color:#a9dfbf;" onclick="window.location.href=';
  echo "'../".$beelogger."/beelogger_show.php'".'"/>&nbsp;&nbsp;';
}
if($MultiType==0){
  echo"&nbsp;&nbsp;";
  $MultiBeeloggerNummer=intval(substr($beelogger,-1));
  echo'<a href="../'.$MultiTypeName.$ServerMultiNumber.'/beelogger_show.php"><input type="button" value="'.$MultiTypeName.' '.$ServerMultiNumber.'" style="background-color:hsl(360,0%,95%);" onclick="window.location.href=';
  echo "'../".$MultiTypeName.$ServerMultiNumber."/beelogger_show.php'".'"/></a>&nbsp;&nbsp;';

  for($i=1;$i <=$MultiTypeAnzahl;$i++){
    echo'<a href="../beelogger'.$MultiSign.$ServerMultiNumber.'_'.$i.'/beelogger_show.php"><input type="button" style="background-color:';
    if($MultiBeeloggerNummer==$i)echo"#a9dfbf";
    else echo"hsl(360,0%,".(100-$i*10).'%)';
    echo';" value="'.$MultiSign.$ServerMultiNumber."- ".$i.'" onclick="window.location.href=';
    echo"'../beelogger".$MultiSign.$ServerMultiNumber."_".$i."/beelogger_show.php'".'"/></a>&nbsp;&nbsp;'."\n";
  }
}

 for($X=1;$X < 4;$X++){
    if(file_exists("../Xanalyse".$X)AND $beelogger !="Xanalyse".$X)echo'&nbsp;&nbsp;<a href="../Xanalyse'.$X.'/beelogger_show.php"><img src="../beelogger_icons/Xanalyse.png" title="Xanalyse'.$X.'" style="margin-bottom:-9px" height=30 width=18 ></a>&nbsp;';
    if(file_exists("../Xanalyse".$X)AND $beelogger=="Xanalyse".$X)echo'&nbsp;&nbsp;<a><img src="../beelogger_icons/Xanalyse_inaktiv.png" title="Xanalyse'.$X.'" style="margin-bottom:-9px" height=30 width=18 ></a>&nbsp;';
 }
 echo"\n";

echo'&nbsp;&nbsp;<a href="../beelogger_mobileWatch.php"><img src="../beelogger_icons/watch.png" title="mobileWatch" style="margin-bottom:-9px" height=30 width=18 ></a>&nbsp;';
 echo"\n";

if($MultiType==-1)$GoToBeelogger="beelogger1";
elseif($MultiType > 1)$GoToBeelogger="beelogger".$MultiTypeName[0].$ServerMultiNumber."_1";
else $GoToBeelogger=$beelogger;
if($mobileCheck_Show=="aktiviert"){
echo'&nbsp;&nbsp;<a href="../beelogger_mobileCheck.php?beelogger='.$GoToBeelogger.'"><img src="../beelogger_icons/mCheck.png" title="mobileCheck" style="margin-bottom:-9px" height=30 width=18 ></a>';
echo"\n";
}
//Anmerkungen Button Array für aktuelle Anmerkungen wurde erzeugt
if($notes_i > 0)echo' <input type="button" style="margin:3px" value="'.$SAs[37].' '.$notes_i.' '.$SAs[38].'" id="AnmerkungenBtn"';
else{
    echo'&nbsp;&nbsp;<input type="button" style="margin:3px" disabled value="'.$SAs[39].'" id="AnmerkungenBtn"';
    $MerkeDassButtonDisabled=true;
}
echo'onclick="AnmerkungBtnPressed()"  title="'.$SAs[40].'"/>';
echo"\n";

//Werte löschen Button
echo'&nbsp;&nbsp;<input type="button" style="margin:3px" value="'.$SAs[41].'" id="WertBtn" onclick="WertBtnPressed()"  title="'.$SAs[42].'">';
echo"\n";

//Konfiguration Button'
if($Passwort==$BeeloggerShowPasswort){//Passwort wurde bereits eingegeben
    echo'<form action="beelogger_show.php" method="post" id="KonfigBtnForm" style="display:inline; font-size: 14px;">';
    echo'&nbsp;&nbsp;<input type="hidden" style="margin:3px" name="passwort" value="'.$Passwort.'">';
    echo"\n";
    echo'<button type="submit" id="KonfigBtnInForm" value="1" title="'.$SAs[44].'" name="config">'.$SAs[43].'</button>';
    echo'</form>';
    echo"\n";
}
else  echo'&nbsp;&nbsp;<input type="button" style="margin:3px" id="KonfigBtn" value="'.$SAs[43].'" onclick="KonfigBtnPressed()"  title="'.$SAs[44].'">';
echo"\n";

echo"&nbsp;".$SAs[45].":&nbsp;<select name='neustandardcsv' style='margin:3px' onChange='document.location.href=this.value'".' title="'.$SAs[46].'">';
echo"\n";
//Listbox csv-dateien
foreach(glob("*.csv")as $filename){
  if(str_contains($filename,"notes")) continue;
  if(file_exists($filename)){
    echo"<option value=beelogger_show.php?csvdatei=".$filename;
    if($filename==$Csvdatei)echo" selected";
    echo">";
    if($filename=="week.csv")echo $SAs[47];
    elseif($filename=="month.csv")echo $SAs[48];
    elseif($filename=="beelogger.csv")echo $SAs[49];
    else echo substr($filename,0,-4);
    echo"</option>\n";
  }
}
echo"</select>\n";
echo"</div>\n";
}//$Config=="0"
//------- ^^^^^  3 Auswahlbuttons -------->

  $IntervallHelp="";
  if($IntervallSendeSteuerung=="lichtgesteuert"){//lichtgesteuerte Sendeintervalle
    if((int)$LetztesLicht > 1)$SendeIntervall=$SommerSendeIntervallTag;//Sonnenlicht vorhanden
    else $SendeIntervall=$SommerSendeIntervallNacht;//nachts --> Sensorwert=0
    if($LetztesLicht=="")$IntervallHelp="zeitgesteuert";//Lichtsteuerung ohne Werte geht nicht
  }

  if($IntervallSendeSteuerung=="solarspannungsgesteuert"){//solarspannungsgesteuerte Sendeintervalle
    if((float)$LetztesVSolar > 0.3)$SendeIntervall=$SommerSendeIntervallTag;//Sonnenlicht vorhanden
    else $SendeIntervall=$SommerSendeIntervallNacht;//nachts --> Sensorwert=0
    if($LetztesVSolar=="")$IntervallHelp="zeitgesteuert";//Spannungsteuerung ohne Werte geht nicht
  }
  
  if($IntervallSendeSteuerung=="zeitgesteuert" OR $IntervallHelp=="zeitgesteuert"){//zeitgesteuerte Sendeintervalle
    if((intval(date("G",$AktualisierungsStamp))>=(int)$SommerTagZeit)AND(intval(date("G",$AktualisierungsStamp))<(int)$SommerNachtZeit))$SendeIntervall=$SommerSendeIntervallTag;//Berechnung(sehr angenähert)für den Sonnen-Auf und Untergang
    else $SendeIntervall=$SommerSendeIntervallNacht;
  }
  
  if($WinterBeginn !="deaktiviert"){
    if(fmod($SommerBeginn, 1)==0.5)$SommerBeginnInTagen=date("z",strtotime(round($SommerBeginn, 0, PHP_ROUND_HALF_DOWN)."/15"));
    else $SommerBeginnInTagen=date("z",strtotime(round($SommerBeginn)."/1"));
    if(fmod($WinterBeginn, 1)==0.5)$WinterBeginnInTagen=date("z",strtotime(round($WinterBeginn, 0, PHP_ROUND_HALF_DOWN)."/15"));
    else $WinterBeginnInTagen=date("z",strtotime(round($WinterBeginn)."/1"));
    if((date("z",$AktualisierungsStamp)< $SommerBeginnInTagen)OR(date("z",$AktualisierungsStamp)> $WinterBeginnInTagen))$SendeIntervall=$WinterSendeIntervall;
  }

//<!-------  Message_box -------->

//Messages erzeugen
if(($Config=="1")OR($Aendern=="1")){//der button zum konfigurieren wurde gedrückt
  if($Passwort !=$BeeloggerShowPasswort)$Message=$SAs[25];
}

if($MultiType !=-1){
 if($Message==""){
  $dtdt=$SAs[127];
  if($col_red)$dtdt .="Y";
  if($AktualisierungStampMessage > 1000)$Message=$SAs[51]." ".date($dtdt,$AktualisierungStampMessage)." ".$SAs[52]." ".date("H:i",$AktualisierungStampMessage).$SAs[53].". ";//nur wenn überhaupt schon Daten vorhanden
  else $Message=$SAs[54]."! ";

  $Mapname="";
  if($MultiType==2)$Mapname="../Duo".intval(substr($beelogger,3,1))."/beelogger_map.php";
  elseif($MultiType==3)$Mapname="../Triple".intval(substr($beelogger,6,1))."/beelogger_map.php";
  elseif($MultiType==4)$Mapname="../Quad".intval(substr($beelogger,4,1))."/beelogger_map.php";
  elseif($MultiType==5)$Mapname="../Penta".intval(substr($beelogger,5,1))."/beelogger_map.php";
  elseif($MultiType==6)$Mapname="../Hexa".intval(substr($beelogger,4,1))."/beelogger_map.php";
  if($Mapname !="")include($Mapname);

 if(strpos($beeloggerSketchID,"LORA"))$IntervallSendeSteuerung="LORA";

 if($Config=="0"){
  //if($IntervallSendeSteuerung !="zeitgesteuert" AND $IntervallSendeSteuerung !="solarspannungsgesteuert" AND $IntervallSendeSteuerung !="lichtgesteuert")$SendeIntervall=15;//keine Serversteuerung
  if(($IntervallSendeSteuerung !="LORA")&&$MultiType >0){
   $Message .=$SAs[55].": ".$SendeIntervall." ".$SAs[61];

   if($IntervallSendeSteuerung=="zeitgesteuert"){
    $Message .=" (";if(strpos($beeloggerSketchID,"EE")!==FALSE)$Message .="EE-"; $Message .=$SAs[56].")";
   }elseif($IntervallSendeSteuerung=="solarspannungsgesteuert")$Message .=" (".$SAs[57].")";
   elseif($IntervallSendeSteuerung=="lichtgesteuert")$Message .=" (".$SAs[58].")";
   else{$Message .=" (".$SAs[59].")";}
  }
  if($IntervallSendeSteuerung !="LORA"){
   $Message .=" / ".$SAs[62]." ";

  $MessageTime=23;
  if($EESendeIntervall=="A" AND $SendeIntervall < 30)$MessageTime=SendeZeit(1);
  if($EESendeIntervall=="A" AND $SendeIntervall >=30)$MessageTime=SendeZeit(2);
  if($EESendeIntervall=="B" AND $SendeIntervall < 30)$MessageTime=SendeZeit(2);
  if($EESendeIntervall=="B" AND $SendeIntervall >=30)$MessageTime=SendeZeit(4);
  if($EESendeIntervall=="C" AND $SendeIntervall < 30)$MessageTime=SendeZeit(4);
  if($EESendeIntervall=="C" AND $SendeIntervall >=30)$MessageTime=SendeZeit(8);
  if($EESendeIntervall=="D" AND $SendeIntervall < 30)$MessageTime=SendeZeit(8);
  if($EESendeIntervall=="D" AND $SendeIntervall >=30)$MessageTime=SendeZeit(16);

  if(date("H",$AktualisierungStampMessage)< 6 AND date("G",$MessageTime)>=6){//Achtung: selbständige Sonderaussendung ab sechster Stunde
   $StartZeit=$AktualisierungStampMessage;
   $Endzeit=date("H",$StartZeit);
   while($Endzeit < 6){
    $StartZeit +=$SendeIntervall*60;
    $Endzeit=date("H",$StartZeit);
   }
   $MessageTime=date("G:i",($StartZeit+$SendeIntervall*60));
  }
  if($MessageTime !=23)$Message .=$MessageTime."&nbsp;-&nbsp;".($MessageTime+1)." ".$SAs[53];
  else $Message .="23 - 0".$SAs[53];
  }//!=LORA
  }//$Config=="0"
 }//$Message==""
}//MultiType

function SendeZeit($Zeitraum){//Zeitraum in Stunden
  global $AktualisierungStampMessage,$SendeIntervall;

  if($Zeitraum==24)return "5:".date("i",$AktualisierungStampMessage);//immer um 5 Uhr

  $JetztStunde=date("H",$AktualisierungStampMessage);
  $StartStunde=$JetztStunde;
  $DannStunde=$JetztStunde+$Zeitraum;
  $LaufStamp=$AktualisierungStampMessage;
  while($JetztStunde < $DannStunde){
    $LaufStamp +=$SendeIntervall*60;
    $JetztStunde=date("H",$LaufStamp);
    if($JetztStunde < $StartStunde)$JetztStunde +=24;//24 Stundenumsprung
  }
  return date("G",$LaufStamp);
}

echo"\n<div id='Message_box' ";if($col_red)echo'style="background-color:#e7846f;"';echo "><span>".$Message."</span></div>\n";

//------ die Sensoren -------->
echo'<div id="Sensorbuttons">'."\n";
//Checkboxen für SensorKurven ---------------------
$Klammern=array("[", "]");

if($MultiType==-1)$GewichtsEinheit="kg";
else $GewichtsEinheit=str_replace($Klammern,"",$HelpArraySensoren[5*5+4]);

$ux_s=sizeof($UseIcon);//fix old data
$ux=$HelpAnzahlSensoren- $ux_s;
if($ux > 0){for($uxx=0;$uxx< $ux;$uxx++){array_push($UseIcon);$UseIcon[$ux_s+$uxx]="false";}}
for($s=0;$s<$HelpAnzahlSensoren;$s++){
 if($HelpArraySensoren[5*$s]=="" AND $s < $HelpAnzahlSensoren){//falls Sensor keinen Namen hat
  echo'<div id="ck-button'.$s.'"><label><input type="checkbox" id="cb'.$s.'" onClick="change(this)"><span></span></label></div>';
 }//if$HelpArraySensoren
 else{//Sensor ist definiert
  if($UseIcon[$s]=="true"){
    echo'<div id="ck-button'.$s.'"><input id="cb'.$s.'" type="checkbox" onClick="change(this)"><label id="cbl'.$s.'" for="cb'.$s.'"></label></div>';
  }else{
    echo'<div id="ck-button'.$s.'"><label><input type="checkbox" id="cb'.$s.'" onClick="change(this)"><span><b>'.$HelpArraySensoren[$s*5].'</b></span></label></div>';
  }
 }
 echo"\n";
}//for
echo'<div id="ck-button'.$s.'"><label><input type="checkbox" id="cb'.$s.'" onClick="change(this)"><span><b>'.$SAs[64].'</b></span></label></div>'."\n";
$s++;

//Value in der Box ist Sensor Nummer oder Wert in der Konfiguration
echo"\n".'<div id="Nummer_Box" title="'.$SAs[64].' '.$SAs[87].'">'."\n";
echo'<select id="tagwertbox" onchange="tageswertanwahl()">';
if(($MultiType==0)||($MultiType==1)){
  $tagwert=false;

  for($t=0;$t < $HelpAnzahlSensoren;$t++){
    if(($t<count($TageswertOptionArray))&&($TageswertOptionArray[$t]=="true" AND $t !=5)){//count -> fix to small array
		echo"\n".'<option value="'.($t+1).'" style="color:'.$HelpArraySensoren[$t*5+1].';"';
		if(($tagwert==false)&&($t==$TageswertAnzeige))echo" selected";
		echo'>'.$HelpArraySensoren[$t*5].'</option>';
		$tagwert=true;
    }
  }
  if($TageswertOptionArray[5]=="true"){
   $tagwert=true;
   if($GewichtsEinheit=="g"){
    for($t=0;$t < 7;$t++){
       switch($t){
		case 0:echo"\n".'<option value="200"';if(!strcmp($TageswertAnzeige,"200"))echo" selected";echo'>200g</option>';break;
		case 1:echo"\n".'<option value="400"';if(!strcmp($TageswertAnzeige,"400"))echo" selected";echo'>400g</option>';break;
		case 2:echo"\n".'<option value="600"';if(!strcmp($TageswertAnzeige,"600"))echo" selected";echo'>600g</option>';break;
		case 3:echo"\n".'<option value="1000"';if(!strcmp($TageswertAnzeige,"1000"))echo" selected";echo'>1000g</option>';break;
		case 4:echo"\n".'<option value="2000"';if(!strcmp($TageswertAnzeige,"2000"))echo" selected";echo'>2000g</option>';break;
		case 5:echo"\n".'<option value="5000"';if(!strcmp($TageswertAnzeige,"5000"))echo" selected";echo'>5000g</option>';break;
		case 6:echo"\n".'<option value="10000"';if(!strcmp($TageswertAnzeige,"10000"))echo" selected";echo'>10000g</option>';break;
      }
     }
   }else{
    if($TageswertAnzeige=="true")$TageswertAnzeige="1.0";//JJ-Abwärtskomp
    for($t=0;$t < 7;$t++){
       switch($t){
		case 0:echo"\n".'<option value="0.2"';if(!strcmp($TageswertAnzeige,"0.2"))echo" selected";echo'>0.2 kg</option>';break;
		case 1:echo"\n".'<option value="0.4"';if(!strcmp($TageswertAnzeige,"0.4"))echo" selected";echo'>0.4 kg</option>';break;
		case 2:echo"\n".'<option value="0.6"';if(!strcmp($TageswertAnzeige,"0.6"))echo" selected";echo'>0.6 kg</option>';break;
		case 3:echo"\n".'<option value="1.0"';if(!strcmp($TageswertAnzeige,"1.0")OR $TageswertAnzeige=="false")echo" selected";echo'>1 kg</option>';break;
		case 4:echo"\n".'<option value="2.0"';if(!strcmp($TageswertAnzeige,"2.0"))echo" selected";echo'>2 kg</option>';break;
		case 5:echo"\n".'<option value="5.0"';if(!strcmp($TageswertAnzeige,"5.0"))echo" selected";echo'>5 kg</option>';break;
		case 6:echo"\n".'<option value="10.0"';if(!strcmp($TageswertAnzeige,"10.0"))echo" selected";echo'>10 kg</option>';break;
       }
      }
    }
  }
  if($tagwert==false){echo'<option value="1.0">1 kg</option>';}//default
}//$MultiType
else{//TW grünland
  for($t=0;$t < $HelpAnzahlSensoren;$t++){
	if($MultiType==2)if($t==5 OR $t==6 OR $t==13 OR $t==14)continue;
	if($MultiType==3)if(($t>4 AND $t<8)OR($t>15 AND $t<19))continue;
	if($MultiType==4)if(($t>4 AND $t<9)OR($t>18 AND $t<23))continue;
	if($MultiType==5)if(($t>4 AND $t<10)OR $t>21)continue;
	if($MultiType==6)if(($t>4 AND $t<11)OR $t>22)continue;
    if(($t<count($TageswertOptionArray))&&($TageswertOptionArray[$t]=="true")){//count -> fix to small array
		echo"\n".'<option value="'.($t+1).'" style="color:'.$HelpArraySensoren[$t*5+1].';"';
		if($t==(int)$TageswertAnzeige)echo" selected";
		echo'>'.$HelpArraySensoren[$t*5].'</option>';
    }
  }
}
echo"\n</select>\n";
echo"</div>\n";


echo"\n".'<div id="ck-button'.$s.'"><label><input type="checkbox" id="cb'.$s.'" onClick="change(this)"><span><b>'.$SAs[65]."</b></span></label>";
echo"</div>"."\n";
  $s++;

if(($MultiType==0)OR($MultiType==1)){//nur für "normale" beelogger
  if($BeutenLeergewicht > 0){
    echo'<div id="ck-button99"><label>';
    echo'<input type="checkbox" id="99"><span>';
    if((((int)$Honigraeume[0]+(int)$Honigraeume[2])> 0)AND(strlen($LetztesGewicht)> 0)){
      echo"<b style='vertical-align:top'> &nbsp;".$SAs[66].":&nbsp;";

      echo round((float)$LetztesGewicht-(float)$BeutenLeergewicht-((int)$Honigraeume[0]*(float)$Honigraeume[1])-((int)$Honigraeume[2]*(float)$Honigraeume[3])-((int)$BeutenUtils[0][0]*(float)$BeutenUtils[0][1])-((int)$BeutenUtils[1][0]*(float)$BeutenUtils[1][1])-((int)$BeutenUtils[2][0]*(float)$BeutenUtils[2][1]),2).$GewichtsEinheit."</b>";
      echo"&nbsp;<img src='../beelogger_icons/Beute.png' width='15' height='15' title='".$SAs[145]."=".$BeutenLeergewicht.$GewichtsEinheit."'>";

      for($i=0;$i <(int)$Honigraeume[0];$i++){
        if((float)$Honigraeume[1] > 100.0)$ShowHonigraum=(float)$Honigraeume[1]/1000;//noch in Gramm
        else $ShowHonigraum=$Honigraeume[1];
        echo"&nbsp;<img src='../beelogger_icons/honigraum.png' width='15' height='".($ShowHonigraum*2)."' title='".$SAs[141]."=".$Honigraeume[1].$GewichtsEinheit."'>";
      }
      for($j=0;$j <(int)$Honigraeume[2];$j++){
        if((float)$Honigraeume[3] > 100.0)$ShowHonigraum=(float)$Honigraeume[3]/1000;//noch in Gramm
        else $ShowHonigraum=$Honigraeume[3];
        echo"&nbsp;<img src='../beelogger_icons/honigraum.png' width='15' height='".($ShowHonigraum*2)."' title='".$SAs[141]."=".$Honigraeume[3].$GewichtsEinheit."'>";
      }
      if((int)$BeutenUtils[0][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Varroaeinschub.png' width='15' height='15' title='".$SAs[142]."=".$BeutenUtils[0][1].$GewichtsEinheit."'>";

      if((int)$BeutenUtils[1][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Absperrgitter.png' width='15' height='15' title='".$SAs[143]."=".$BeutenUtils[1][1].$GewichtsEinheit."'>";

      if((int)$BeutenUtils[2][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Futterzarge.png' width='15' height='15' title='".$SAs[144]."=".$BeutenUtils[2][1].$GewichtsEinheit."'>";
    }else{
      echo"<b style='vertical-align:top'>&nbsp;".$SAs[67].":";
      $G_korr=(float)$LetztesGewicht-(float)$BeutenLeergewicht-((int)$Honigraeume[0]*(float)$Honigraeume[1])-((int)$Honigraeume[2]*(float)$Honigraeume[3]);
      if((int)$BeutenUtils[0][0]==1)$G_korr=$G_korr -(float)$BeutenUtils[0][1];
      if((int)$BeutenUtils[1][0]==1)$G_korr=$G_korr -(float)$BeutenUtils[1][1];
      if((int)$BeutenUtils[2][0]==1)$G_korr=$G_korr -(float)$BeutenUtils[2][1];
      echo round($G_korr,1).$GewichtsEinheit."</b>";
      if((int)$BeutenUtils[0][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Varroaeinschub.png' width='15' height='15' title='".$SA[142]."=".$BeutenUtils[0][1].$GewichtsEinheit."'>";
      if((int)$BeutenUtils[1][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Absperrgitter.png' width='15' height='15' title='".$SA[143]."=".$BeutenUtils[1][1].$GewichtsEinheit."'>";
      if((int)$BeutenUtils[2][0]==1)echo"&nbsp;<img src='../beelogger_icons/n_Futterzarge.png' width='15' height='15' title='".$SA[144]."=".$BeutenUtils[2][1].$GewichtsEinheit."'>";
    }
    echo"</span></label></div>"."\n";
  }
}else{//Dummybutton um die Symbole auszurichten falls nur Symbole verwendet werden
    echo'<div id="ck-button999"><label>';
    echo'<input type="checkbox" id="999" style="display:none"';
    echo'<span></span></label></div>'."\n";
}
//<!-- ^^^^ die Sensoren -------->

echo'<div id="AlleAuswahlbutton"> <label><input type="checkbox" id="cb'.$s.'" onClick="change(this)"><span>&nbsp;'.$SAs[68].'&nbsp;</span></label></div>'."\n\n";

echo"\n".'<div id="trenner"><span>&nbsp;</span></div>'."\n";//button reihen trennen

//!-- ^^^^ Navigation -------->
echo'<div id="NavigationAnzeige"><span title="'.$SAs[73].'">&nbsp;&nbsp;</span>'."\n";
  if($Csvdatei[0]=='w'){//week: 1h, 2h, 4h, 8h, 24h, 1/2w,
  echo'<input id="nav1"; type="button" style="background-color:#FAFAFA;"value="1 h" onclick="zoom(86400/24);">';
  echo'<input id="nav2"; type="button" style="background-color:#F2F2F2;"value="2 h" onclick="zoom(86400/12);">
  <input id="nav4"; type="button" style="background-color:#E6E6E6;"value="4 h" onclick="zoom(86400/6);">';
  echo'<input id="nav8"; type="button" style="background-color:#D8D8D8;"value="8 h" onclick="zoom(86400/3);">
  <input id="nav24"; type="button" style="background-color:#BDBDBD;"value="'.$SAs[69].'" onclick="zoom(86400);">';
  echo'<input id="nav3d"; type="button" style="background-color:#A4A4A4;"value="1/2 '.$SAs[70].'" onclick="zoom(3.5 * 86400);">';
  }else if($Csvdatei[0]=='m'){//month: 2h, 4h, 8h,24h, 7d, 14d
  echo'<input id="nav2"; type="button" style="background-color:#F2F2F2;" value="2 h" onclick="zoom(86400/12);">
  <input id="nav4"; type="button" style="background-color:#E6E6E6;" value="4 h" onclick="zoom(86400/6);">';
  echo'<input id="nav8"; type="button" style="background-color:#D8D8D8;" value="8 h" onclick="zoom(86400/3);">
  <input id="nav24"; type="button" style="background-color:#BDBDBD;" value="'.$SAs[69].'" onclick="zoom(86400);">';
  echo'<input id="nav7d"; type="button" style="background-color:#BDBDBD;"value="'.$SAs[70].'" onclick="zoom(7 * 86400);">';
  echo'<input id="nav14d"; type="button" style="background-color:#BDBDBD;"value="14 '.$SAs[71].'" onclick="zoom(14 * 86400);">';
  }else if($Csvdatei[0]=='b'){//gesamt: 2,4,8,24, week, 14 day, month, 3 month
  echo'<input id="nav2"; type="button" style="background-color:#F2F2F2;" value="2 h" onclick="zoom(86400/12);">
  <input id="nav4"; type="button" style="background-color:#E6E6E6;" value="4 h" onclick="zoom(86400/6);">';
  echo'<input id="nav8"; type="button" style="background-color:#D8D8D8;" value="8 h" onclick="zoom(86400/3);">
  <input id="nav24"; type="button" style="background-color:#BDBDBD;" value="'.$SAs[69].'" onclick="zoom(86400);">';
  echo'<input id="nav7d"; type="button" style="background-color:#BDBDBD;"value="'.$SAs[70].'" onclick="zoom(7 * 86400);">';
  echo'<input id="nav14d"; type="button" style="background-color:#BDBDBD;"value="14 '.$SAs[71].'" onclick="zoom(14 * 86400);">';
  echo'<input id="nav30d"; type="button" style="background-color:#848484;" value="'.$SAs[72].'" onclick="zoom(30 * 86400);">';
  echo'<input id="nav90d"; type="button" style="background-color:#848484;" value="3 '.$SAs[72].'" onclick="zoom(90 * 86400);">';
  }else if($Csvdatei[0]=='A'){//archiv:  8h, 24h , 7d, month, 3 month
  echo'<input id="nav8"; type="button" style="background-color:#D8D8D8;" value="8 h" onclick="zoom(86400/3);">
  <input id="nav24"; type="button" style="background-color:#BDBDBD;" value="'.$SAs[69].'" onclick="zoom(86400);">';
  echo'<input id="nav7d"; type="button" style="background-color:#BDBDBD;"value="'.$SAs[70].'" onclick="zoom(7 * 86400);">';
  echo'<input id="nav30d"; type="button" style="background-color:#848484;" value="'.$SAs[72].'" onclick="zoom(30 * 86400);">';
  echo'<input id="nav90d"; type="button" style="background-color:#848484;" value="3 '.$SAs[72].'" onclick="zoom(90 * 86400);">';
  }

echo'
  <input type="button" style="background-color:#6E6E6E;" value="Reset Zoom" onclick="reset_Zoom();">

  <span title="'.$SAs[73].':">&nbsp;&nbsp;Scroll:&nbsp;</span>
  <input type="button" style="background-color:#E6E6E6;" value="|<" onclick="panend(-1);" title="'.$SAs[74].'">
  <input type="button" style="background-color:#F2F2F2;" value="<<" onclick="pan(-1);">
  <input type="button" style="background-color:#FAFAFA;" value="<"  onclick="pan(-0.5);"  title="'.$SAs[75].'">
  <input type="button" style="background-color:#FAFAFA;" value=">"  onclick="pan(0.5);"   title="'.$SAs[76].'">
  <input type="button" style="background-color:#F2F2F2;" value=">>" onclick="pan(1);">
  <input type="button" style="background-color:#E6E6E6;" value=">|" onclick="panend(1);"  title="'.$SAs[77].'">&nbsp;&nbsp;
  <input id="123" type="button" value="'.$SAs[81].'" onclick="show_points()" title="'.$SAs[78].'">&nbsp;
  <input id="124" type="button" value="'.$SAs[82].'" onclick="set_legend()" title="'.$SAs[79].'">
  </div>';

if(file_exists($WechselIniName)){
if($WechselIniName !="")include($WechselIniName);}

if($LetztesVBatt > 3.0){
  if($AkkuLeerSchwelle !=0 && $AkkuVollSchwelle !=0 && $LetztesVBatt !=""){
   echo'&nbsp;&nbsp;&nbsp;&nbsp;<img ';
   if($LetztesVBatt >=$AkkuVollSchwelle)echo'src="../beelogger_icons/Akku100.png"';
   elseif($LetztesVBatt < $AkkuLeerSchwelle)echo'src="../beelogger_icons/Akku25.png"';
   else echo'src="../beelogger_icons/Akku50.png"';
   echo' width="26" height="12" style="margin-top:22px" title="Bat.: '.$LetztesVBatt.'V">';
  }
}

include("beelogger_ini.php");//REINIT
if($TageswertAchse=="")$TageswertAchse="y2";//Abwärtskomp

echo'<div id="BL_grafik"> </div>
</div>'."\n\n";//<!-- div Sensorbuttons -->

//<!------- FORM Passwortabfrage zur Konfig -------->
echo'<div id="DatenAreaKonfig">
<form action="beelogger_show.php" method="post" id="KonfigPasswortEingabeForm" style="display:none;font-size: 14px;">'.$SAs[80].':
<input type="password" name="passwort" size="5">
&nbsp;&nbsp;
<button type="submit" value="1" name="config"><b>'.$SAs[83].'</b></button>
<button type="reset" onclick="AktionAbbruch()" style="background-color: #e7846f;" name="cancelAnmerkungBearbeiten" value="0"><b>'.$SAs[84].'</b></button>
</form>
</div> '."\n\n";
//<!------- Ende FORM Passwortabfrage zur Konfig ------>


//<!------- FORM für Neue Anmerkung -------->
echo'<div id="DatenArea">
  <form action="beelogger_show.php" method="post" id="AnmkForm" style="display:none;font-size: 14px;">
  <span title="'.$SAs[85].'."><b>'.$SAs[86].':</b></span>
  <input id="Sensor_anno" name="sensor" type="text" style="width:103px;" value="Sensor_anno" title="'.$SAs[87].'"/>
  <input id="Datum_anno" type="text" style="width:115px;" value="" title="'.$SAs[88].'"/>
  <input id="Termin_anno" name="termin" type="hidden" />
  <input id="K_anno" name="kurztext" type="text" maxlength="20" size="12" value="" title="'.$SAs[89].'"/>';
 echo'<select name="note_icon">';
 echo'<option value="" selected>'.$SAs[135].'</option>';

 $dir="../beelogger_icons";
 $files=scandir($dir);
 foreach($files as $PNGs){
  if(substr($PNGs,0,2)=="n_"){
    echo'<option value="../beelogger_icons/'.$PNGs.'">'.$SAs[136].': ';
    if($Sprache=="1")echo substr(substr($PNGs,2),0,-4);
    else{
//echo $IconBezeichner[0][$Sprache];
      $i=0;
      while($i < sizeof($IconBezeichner)){
        $Gefunden=false;
        if($PNGs==$IconBezeichner[$i][1]){
          echo $IconBezeichner[$i][$Sprache];
          $Gefunden=true;
          break;
        }
        $i++;
      }
      if($Gefunden==false)echo substr(substr($PNGs,2),0,-4);
    }
  echo'</option>';
  }
 }
 echo'</select>&nbsp;&nbsp;';

 echo'<input id="Edit_anno" name="langtext" type="text" value="" title="'.$SAs[90].'"/>
 &nbsp;&nbsp;';

if($Passwort==$BeeloggerShowPasswort){//Es wurde bereits ein korrektes Passwort in der Session eingegeben
  echo"<input type='hidden' name='passwort' value='".$Passwort."'>";
}
else{
  echo $SAs[91].': <input type="password" name="passwort" size="5">';
}
echo'
<input type="hidden" name="csvdatei" value="'.$Csvdatei.'">&nbsp;&nbsp;
<button type="submit" name="erzeugen" value="1" title="'.$SAs[92].'"><b>'.$SAs[93].'</b></button>&nbsp;&nbsp;
<button type="reset" onclick="AktionAbbruch()" style="background-color: #e7846f;" name="cancelAnmerkungErzeugen" value="0"><b>'.$SAs[84].'</b></button>
</form>
</div>'."\n\n";
//<!------- Ende FORM für Neue Anmerkung -------->

//<!------- FORM zum Löschen eines Wertes -------->
echo'<div id="DatenAreaLoeschWert">
  <form action="beelogger_show.php" method="post" id="WertloeschenForm" style="display:none;font-size: 14px;">';
  if(($Csvdatei=="beelogger.csv")OR($Csvdatei=="month.csv")OR($Csvdatei=="week.csv")){
  echo'
  <span title="'.$SAs[94].'."><b>'.$SAs[95].':</b></span>
  <input id="Sensor_annoL" name="sensor" type="text" style="width:103px;" value="" title="'.$SAs[87].'">
  <input id="Datum_annoL" type="text" style="width:115px;" value="" title="'.$SAs[88].'">
  '.$SAs[97].'
  <input id="WertL" name="neuwert" type="text" style="width:50px;" value="" title="'.$SAs[96].'">
  <input id="Termin_annoL" name="termin" type="hidden"><b>&nbsp;&nbsp;</b>';

 if($Passwort==$BeeloggerShowPasswort){//Es wurde bereits ein korrektes Passwort in der Session eingegeben
  echo"<input type='hidden' name='passwort' value='".$Passwort."'>";
 }
 else{
  echo $SAs[91].': <input type="password" name="passwort" size="5" required>';
 }
 echo"<input type='hidden' name='csvdatei' value='".$Csvdatei."'>";//falls gewechselt wurde - mitsenden

 echo'&nbsp;&nbsp;<button type="submit" name="wertloeschen" value="1" title="'.$SAs[98].'!"><b>'.$SAs[99].'</b></button>
<button type="reset" onclick="AktionAbbruch()" name="nichts" style="background-color: #e7846f;" value=""><b>'.$SAs[84].'</b></button>';
}//falls beelogger.csv oder month.csv geladen und nicht Archivdatei
else echo'<b><font size="3">This function is not available for archived data!</b>';

echo'
</form>
</div>';
//<!------- Ende FORM zum Löschen eines Wertes -------->

//Formular zum Ändern einer Anmerkung wurde abgeschickt / bekommt $Termin=Datumstamp---------------------
if($Aendern=="1"){
 if($Passwort==$BeeloggerShowPasswort){
echo'
 <div id="DatenAreaAnmerkAend">
 <form action="beelogger_show.php" method="post" id="FormAendAnmk"  style="display:block;font-size: 14px;">
 <b>'.$SAs[100].': </b>';
  $TerminAnzahl=1000;//Anzahl, wieviele Termine ausgelesen werden
  $i=0;
  while($i < sizeof($narray)){
  $Zeile=trim($narray[$i]);
  $nx=explode(",", $Zeile);
  $ns=sizeof($nx);
  $ZeilenDatumStamp=$nx[$ns-1];
  if($ZeilenDatumStamp==$Termin)break;
  $i++;
  }

  $note=explode("&",$nx[2]);
  echo'<select name="sensor">';
  $Sensor=$nx[0];//alten Sensor gelesen
  for($s=0;$s < $AnzahlSensoren;$s ++){
    echo"<option value='".$Sensor."%".$s."'";
    if($Sensor==$s)echo" selected";
    echo">".$Sensoren[$s*5]."</option>\n";
  }
  echo"</select>";

//DATUM
  if($NummerLetzteZeile <=$TerminAnzahl)$TerminAnzahl=$NummerLetzteZeile;
  echo'<select name="termin">';

  $TerminWarDabei=FALSE;//
  for($u=$NummerLetzteZeile;$u >($NummerLetzteZeile-$TerminAnzahl);$u--){
  $what=trim($array[$u]);
  $x=explode(",", $what);
  $s=sizeof($x);
  echo"<option value=".$nx[$ns-1]."%".$x[$s-1];
  if($nx[$ns-1]==$x[$s-1]){
    echo" selected ";
    $TerminWarDabei=TRUE;
  }
  echo">".$x[0]."</option>";//timestamp reicht aus
  }//for $u

  if(!$TerminWarDabei){//der Termin war nicht in der letzten Woche
  echo"<option value=".$nx[$ns-1]."%".$nx[$ns-1];
  echo" selected ";
  echo">".date('Y/m-d H:i:s',$nx[$ns-1])."</option>";//timestamp reicht aus
  }

  echo"</select>&nbsp;&nbsp;";

//KÜRZEL
  if(strpos($note[0],".png")> 0)echo $SAs[101].": <input type='text' name='kurztext' value='?' size='8' maxlength='20'>";
  else echo $SAs[101].": <input type='text' name='kurztext' value='".$note[0]."' size='12' maxlength='20'>";

  echo'<select name="note_icon">';
  $dir="../beelogger_icons";
  $files=scandir($dir);
  echo"<option value=''>".$SAs[135]."</option>";
  foreach($files as $PNGs){
  if(substr($PNGs,0,2)=="n_"){
    $ShowIcon='../beelogger_icons/'.$PNGs;
    echo'<option value="../beelogger_icons/'.$PNGs.'"';
    if($note[0]==$ShowIcon)echo" selected ";
    echo'>'.$SAs[136].': ';
    if($Sprache=="1")echo substr(substr($PNGs,2),0,-4);
    else{
//echo $IconBezeichner[0][$Sprache];
      $i=0;
      while($i < sizeof($IconBezeichner)){
        $Gefunden=false;
        if($PNGs==$IconBezeichner[$i][1]){
          echo $IconBezeichner[$i][$Sprache];
          $Gefunden=true;
          break;
        }
        $i++;
      }
      if($Gefunden==false)echo substr(substr($PNGs,2),0,-4);
    }
    echo'</option>';
  }
  }
  echo'</select>&nbsp;&nbsp;';

  echo $SAs[139].': ';
  echo"<input type='text' name='langtext' value='".$note[1]."'size='20'></td>";
  echo"<input type='hidden' name='passwort' value='".$Passwort."''>";//Passwort auch übertragen
  echo"<input type='hidden' name='csvdatei' value='".$Csvdatei."'>";//falls gewechselt wurde - mitsenden
  echo'<button type="submit" name="speichern" id="AendAnmkBtn" value="1"><b>'.$SAs[102].'</b></button>';
  echo'<button type="reset" onclick="AktionAbbruch()" style="background-color: #e7846f;" name="cancelAnmerkungÄndern" value="0"><b>'.$SAs[84].'</b></button>';
  echo'</form></div>';
 }//if$passwort
}//ifaendern=1
//Ende Verarbeiten Formular ändern -----------------------------------------------

//<!------- FORM zum Ändern/Löschen von Anmerkungen : gibt termin aus(Stamp der Anmerkung)-------->
echo'<div id="DatenAreaAendAnmrk">
<form action="beelogger_show.php" method="post" id="LoeAenForm" style="display:none;font-size: 14px;">';

if($notes_i > 0){//nur wenn mind. eine Anmerkung existiert
  echo "\n<select name='termin'>\n";
  for($o=$notes_i;$o >=0;$o--){
  $what=trim($narray[$o]);
  $x=explode(",", $what);
  $s=sizeof($x);
  $note=explode("&",$x[$s-2],2);
  if($s > 1){
    $AnmrkDatum=$x[$s-1];
    echo"<option value=".$AnmrkDatum.">".$SAs[87].": ";
    if(is_numeric($x[0]))echo $Sensoren[$x[0]*5];
    else echo $x[0];
    echo" ".$x[1]." ";
    if(strpos($note[0],".png")> 0){
      echo $SAs[136].": ";
      if($Sprache=="1")echo substr(substr($note[0],21),0,-4);
      else{
        $i=0;
        while($i < sizeof($IconBezeichner)){
          $Gefunden=false;
          if(substr($note[0],19)==$IconBezeichner[$i][1]){
            echo $IconBezeichner[$i][$Sprache];
            $Gefunden=true;
            break;
          }
          $i++;
        }
        if($Gefunden==false)echo substr(substr($note[0],21),0,-4);
      }
    }
    else echo $SAs[101].": ".$note[0];
    if($note[1] !="" AND $note[1] !=$SAs[26])echo" ".$SAs[103].": ".$note[1]."</option>\n";
  }
  }//for $o

 echo'</select>';
 if($Passwort==$BeeloggerShowPasswort){//Es wurde bereits ein korrektes Passwort in der Session eingegeben
 echo"<input type='hidden' name='passwort' value='".$Passwort."'>";
 }
 else{
   echo"\n".'Passwort: <input type="password" name="passwort" size="5">&nbsp;&nbsp;';
 }
 echo"<input type='hidden' name='csvdatei' value='".$Csvdatei."'>";//falls gewechselt wurde - mitsenden
 echo'<button type="submit" name="aendern"  value="1"><b>'.$SAs[99].'</b></button>&nbsp;&nbsp;';
 echo'<button type="submit" name="loeschen"  value="1"><b>'.$SAs[104].'</b></button>&nbsp;&nbsp;';
 echo'<button type="reset" onclick="AktionAbbruch()" style="background-color: #e7846f;" name="cancelAnmerkungBearbeiten" value="0"><b>'.$SAs[84].'</b></button>';
}//if$notes_i >0
echo "</form></div>";
//ENDE FORM Anmerkungen löschen und ändern----------------------------------

//Konfig ändern --------------------------------------------
if($Config=="1"){//der button zum konfigurieren wurde gedrückt
    if($Passwort==$BeeloggerShowPasswort){
      include("beelogger_config.php");
  }
}//else config=="0"
else{
  if($Passwort_Show_Counter >=1){
    echo'<script language="javascript">';
    echo'alert("'.$SAs[106].': ';
    for($i=0;$i <($Passwort_Show_Counter-1);$i++){
      echo $AlertArray[$i].", ";
    }
    echo $AlertArray[$i];
    echo'")';
    echo'</script>';
  }
}//ifconfig=="0"
?>

<!-- Dygraphsbereich Start -->

<script type="text/javascript" charset="UTF-8">

//globale Variablen festlegen
var Werteloeschen=false;
var BL;//die dygraph Objecte
var desired_range=null;//Anzeige/Zoom Bereich für Dygraph
var move=1;//Anzahl der Schritte zum desired_range begrenzen
var Ax2Rng=0;//Variable die anzeigt, wieviele Kurven angezeigt werden
var data_d=[];//neue Datenstruktur
var tag_setup=0;//Tageswerte berechnet ?
var summe_setup=0;//Summenwerte berechnet ?
var GTS=0;
var roll_period=<?php echo $RollPeriod; ?>;
var ann_count=0;
var LoeschenButton=0;//Zustand des LoeschenButtons 0=nicht gedrückt
var winH=window.innerHeight;//das Fenster an sich

<?php
$mobilePhone=0;//Mobilgeräte
if(preg_match("/(alcatel|amoi|android|avantgo|blackberry|benq|cell|cricket|docomo|elaine
|htc|iemobile|iphone|ipad|ipaq|ipod|j2me|java|midp|mini|mmp|mobi|motorola|nec-|nokia|palm|
panasonic|philips|phone|playbook|sagem|samsung|sharp|sie-|silk|smartphone|sony|symbian|t-mobile|telus
|up\.browser|up\.link|vodafone|wap|webos|wireless|xda|xoom|zte)/i", $_SERVER['HTTP_USER_AGENT']))
{ $mobilePhone=1;}
if($PunktAnzeige=="true")echo'var points_show=1;document.getElementById("123").style.backgroundColor="green";';
else  echo'var points_show=0;'; ?>

var d_names=[<?php echo'"'.$SAs[107].'","'.$SAs[108].'","'.$SAs[109].'","'.$SAs[110].'","'.$SAs[111].'","'.$SAs[112].'","'.$SAs[113].'"'; ?>];
var m_names=[<?php echo'"'.$SAs[114].'","'.$SAs[115].'","'.$SAs[116].'","'.$SAs[117].'","'.$SAs[118].'","'.$SAs[119].'","'.$SAs[120].'","'.$SAs[121].'","'.$SAs[122].'","'.$SAs[123].'","'.$SAs[124].'","'.$SAs[125].'"'; ?>];
var EinzelSensoren=[<?php for($e=0;$e < $HelpAnzahlSensoren;$e++)echo'"'.$HelpArraySensoren[$e*5].'",'; echo'"'.$SAs[147].'+","'.$SAs[147].'-","'.$SAs[65].'"';?>];
var EinzelEinheiten=[<?php for($e=0;$e < $HelpAnzahlSensoren;$e++)echo"'".$HelpArraySensoren[$e*5+4]."',"; echo"'[".$GewichtsEinheit."]','[".$GewichtsEinheit."]','[".$GewichtsEinheit."]']";?>;

const tws=[180,280,350,500,550,700,850,1000,1100,1200,1400,1550,1552];

try{<?php echo "window.top.document.title=' ".$BienenvolkbezeichnungToEcho."';";?>} catch(error){}//whatever

//my_onresize: resize Event Grafik an Fenster anpassen
function my_onresize(){
var rect=document.getElementById("BL_grafik").getBoundingClientRect();
var w=window.innerWidth-30;//das Fenster an sich
var h=window.innerHeight;
var hh=(h - rect.top - 40);
<?php if($mobilePhone==1)echo "if(w > h){ if((winH - h)>100)winH=h; hh=winH+50; };";?>
if(typeof BL==='undefined'){return;}
BL.resize(w,hh);
}

<?php
if($Aendern=="1"){//es soll eine Anmerkung geändert werden
  echo"document.getElementById('Message_box').textcontent=' ';";
  echo"document.getElementById('WertBtn').disabled=true;";
  echo"document.getElementById('AnmerkungenBtn').disabled=true;";
  }
?>

function KonfigBtnPressed(){//Konfiguration Button ohne Passwort gedrückt
  Werteloeschen=false;
  document.getElementById('Message_box').textContent="-";
  document.getElementById('WertBtn').disabled=true;
  document.getElementById('AnmerkungenBtn').disabled=true;
  document.getElementById('KonfigPasswortEingabeForm').style.display="block";//FORM ZEIGEN
  document.getElementById('LoeAenForm').style.display="none";//FORM Löschen Ändern Anmerkung AUS
  document.getElementById('AnmkForm').style.display="none";//FORM Neue Anmerkung AUS
  document.getElementById('WertloeschenForm').style.display="none";//FORM AUS
}

function AnmerkungBtnPressed(){//Löschen bzw Ändern von Anmerkungen Button gedrückt
  document.getElementById('Message_box').textContent="-";
  document.getElementById('WertBtn').disabled=true;
  document.getElementById('AnmerkungenBtn').disabled=true;
  document.getElementById('LoeAenForm').style.display="block";//FORM Löschen ändern Anmerkung AN
  document.getElementById('AnmkForm').style.display="none";//FORM AUS
  document.getElementById('WertloeschenForm').style.display="none";//FORM AUS
}

function WertBtnPressed(){//Button Wert Löschen/ändern gedrückt
  Werteloeschen=true;
  document.getElementById('Message_box').textContent="-";
  document.getElementById('WertBtn').disabled=true;
  document.getElementById('AnmerkungenBtn').disabled=true;
  document.getElementById('WertloeschenForm').style.display="block";//FORM Löschen/ändern für Werte ZEIGEN
  document.getElementById('LoeAenForm').style.display="none";//FORM AUS
  document.getElementById('AnmkForm').style.display="none";//FORM AUS
}

function AktionAbbruch(){//Abruchbutton in Form gedrückt(Default herstellen)
  Werteloeschen=false;
  document.getElementById("WertBtn").disabled=false;
  document.getElementById("Message_box").textContent=<?php echo'"'.$SAs[84].'"';?>;//echo".";
  <?php
  if($Passwort !=$BeeloggerShowPasswort)echo"document.getElementById('KonfigBtn').disabled=false;";//Passwort
  if($MerkeDassButtonDisabled !=true)echo"document.getElementById('AnmerkungenBtn').disabled=false;";
  ?>
  document.getElementById('LoeAenForm').style.display="none";//FORM AUS
  <?php if($Aendern=="1")echo"document.getElementById('FormAendAnmk').style.display='none';";
  ?>
  document.getElementById('AnmkForm').style.display="none";
  document.getElementById('WertloeschenForm').style.display="none";
  document.getElementById('KonfigPasswortEingabeForm').style.display='none';
}

<?php
 if($Legende=="immer")echo'document.getElementById("124").style.backgroundColor="green";';
   else if($Legende=="folgend")echo'document.getElementById("124").style.backgroundColor="grey";';
     else echo'document.getElementById("124").style.backgroundColor="lightgrey";';
//Mouseover fuer Icon erzeugen//aktiviere Buttons
  for($i=0;$i < $HelpAnzahlSensoren;$i++){
    echo"\n".'document.getElementById("cb'.$i.'").checked='.$HelpArraySensoren[$i*5+2].';';
	if($i<count($UseIcon)){//fix to small array
      if($UseIcon[$i]=="true")echo"\n".'document.getElementById("cbl'.$i.'").setAttribute("title", "'.html_entity_decode($HelpArraySensoren[$i*5]).'");';
	}
  }

if($MultiType==-1){
  if($Config=="0"){
  echo"\n"."document.getElementById('WertBtn').disabled=true;";
  echo"\n"."document.getElementById('AnmerkungenBtn').disabled=true;";
  }
}

//nicht konfig-Mode, dann grafik
if(($Config=="0")OR($Passwort !=$BeeloggerShowPasswort)){
echo"\n";
$y_ticks=1;//data only on y-axes
for($i=0;$i<$HelpAnzahlSensoren;$i++){if(strpos($HelpArraySensoren[$i*5+3],"y2")>0)$y_ticks=0;}
?>

var BL=new Dygraph(document.getElementById("BL_grafik"),
  <?php
  if(file_exists($Csvdatei)){
    $array=file($Csvdatei);$i=sizeof($array);
    for($x=0;$x<$i;$x++){$what=bl_grafikzeile($array[$x]);echo '"'.$what.'\n"';if($x<$i-1)echo '+';}//eigen-utc-1
  }
  else echo'"2022-10-01,,,,,,,,,,,,,,,,\n" + "2022-10-06 10:00,30,,,,,,30,,30,,,,,,,\n"+ "2022-10-06 22:00,,20,,,,,,,,,,,,,,\n" + "2022-10-07 10:0,11,,,,,,11,,,20,,,,,,\n" + "2022-10-09,10,23,,,,,10,,,,,,,,,\n"+ "2022-10-11,10,23,10,,,,,,,,,,,,,\n" + "2022-10-13,17,17,,,,,,,,,,,,,,\n" + "2022-10-14,,,12,19,19,,,,,,19,,,,,\n" + "2022-10-16,,,,,23,,,,,,,,,,,\n" + "2022-10-18,,,16,11,23,,,,,,11,,,,,\n" + "2022-10-20,,,19,10,19,,,,,,10,,,,,\n" + "2022-10-22,,,,,,19,,19,,,,,,,,\n"+ "2022-10-24,,,,,,23,,13,,,,,,,,\n" + "2022-10-26,,,,16,,23,,11,,,16,,,,,\n" +"2022-10-28,,,,19,,19,,10,,,19,,30,,,\n" + "2022-11-02,,,,,,,,,,,,,,,,\n"'; ?>,
//Optionen
{
  labels: ["Datum",<?php for($s=0;$s < $HelpAnzahlSensoren;$s++){ echo'"'.html_entity_decode($HelpArraySensoren[$s*5]).' '.html_entity_decode($HelpArraySensoren[$s*5+4]).'",'; }
  echo'"'.$SAs[147].'+","'.$SAs[147].'-","'.$SAs[65].'"],'."\n";?>
  colors: [<?php for($s=0;$s < $HelpAnzahlSensoren;$s++){ echo"'".$HelpArraySensoren[$s*5+1]."',"; }
  echo"'#00ff01','#ff0001','orange'],\n";?>
  visibility: [<?php for($s=0;$s < $HelpAnzahlSensoren;$s++){ echo $HelpArraySensoren[$s*5+2].","; }?>false,false,false],
  xlabel:'',ylabel:'',y2label:'',
  series :{
  <?php for($s=0;$s < $HelpAnzahlSensoren;$s++){
  echo'"'.html_entity_decode($HelpArraySensoren[$s*5]).' '.html_entity_decode($HelpArraySensoren[$s*5+4]).'":{axis:'.$HelpArraySensoren[$s*5+3].'';
  if(strlen($FillGraph[$s])>2){echo',drawPoints:false,pointSize:1,fillGraph:true,fillAlpha:'.$FillGraph[$s];}
  echo'},'."\n";
  }
  echo '"'.$SAs[147].'+":{axis:"'.$TageswertAchse.'",drawPoints:false,pointSize:1,fillGraph:true,fillAlpha:0.5},
  "'.$SAs[147].'-":{axis:"'.$TageswertAchse.'",drawPoints:false,pointSize:1,fillGraph:true,fillAlpha:0.5},
  "'.$SAs[65].'":{axis:"'.$TageswertAchse.'",drawPoints:false,pointSize:1,fillGraph:true,fillAlpha:0.2}';?>
  },
  axes:{
  x:{axisLabelFormatter:function(d,gran){
    var curr_month=m_names[d.getMonth()];
    var curr_day=d_names[d.getDay()];
	if(gran < 20){
	 var Hrs=d.getHours();
	 var Minuten=d.getMinutes();
	 var Mins=((Minuten<10)?"0"+Minuten:Minuten);
	 var hr=1;
	 if(Minuten==0){hr=Hrs%8;if(gran<18)hr=Hrs%4;if(gran<17)hr=Hrs%2;if(gran<16)hr=0;}
	 if(gran<15)hr=Minuten%30;
	 if(hr==0)return(curr_day+" "+d.getDate()+"<?php echo $SAs[128].'"+curr_month+"'.$SAs[128]?>"+" "+Hrs+":"+ Mins);
	 else return(Hrs+":"+Mins);
	}
    return curr_day+" "+d.getDate()+"<?php echo $SAs[128]?>"+curr_month;
    },
    axisLabelWidth:160,pixelsPerLabel:110
  },
  y:{drawGrid:true,independentTicks:<?php if(($TwoGrid=='true')OR($y_ticks==1)){ echo"true";echo",gridLinePattern: [5,5]";}else echo"false";?>,axisLabelWidth:60,pixelsPerLabel:30,digitsAfterDecimal:2,
  axisLabelFormatter:function(x){if(Math.abs(x)<0.01)return "0-";if(Math.abs(x)<10.0)return(Math.round(x*100,2)/100);if(x>500)return(Math.round(x));return(Math.round(x*10,1)/10);}},
  y2:{drawGrid:true,independentTicks:true,axisLabelWidth:60,pixelsPerLabel:30,<?php if($RollPeriod !=1)echo"digitsAfterDecimal:2,"; else echo"digitsAfterDecimal:3";?>}},
  hideOverlayOnMouseOut:false,
  connectSeparatedPoints:true,strokeWidth:2,
  showRoller:true,rollPeriod:<?php echo $RollPeriod; ?>,
  drawPoints:<?php if($PunktAnzeige=="true")echo"true,"; else echo"false,"; ?>
  displayAnnotations:true,
  highlightSeriesOpts:{strokeWidth:2,strokeBorderWidth:1,highlightCircleSize:4},
  underlayCallback: function(canvas, area, g){
    if(typeof BL==='undefined'){return;}
	var ax=0;<?php if($TageswertAchse=="y2")echo "ax=1;";
     if($GTS_color=="true")
      echo " if((GTS==1)&&(g.toDomYCoord(tws[0],ax)> 0)){
     var ya,yb;
  	 canvas.font='14px Arial';
     for(var x=0; x<12; x++){
	  canvas.fillStyle=`#000000`;
      ya=g.toDomYCoord(tws[x],ax);if(ya<0)break;yb=g.toDomYCoord(tws[x+1],ax);if(yb<0)yb=0;yb=yb-ya;
      if(x==0){canvas.fillText('Weide',area.x,ya);canvas.fillStyle=`rgba(246,241,106, 0.4)`;}
      if(x==1){canvas.fillText('Schlehe',area.x,ya);canvas.fillStyle=`rgba(106,246,176, 0.4)`;}
      if(x==2){canvas.fillText('  ',area.x,ya);canvas.fillStyle=`rgba(106,246,176, 0.0)`;}
      if(x==3){canvas.fillText('Kirsche',area.x,ya);canvas.fillStyle=`rgba(246,115,106, 0.5)`;}
      if(x==4){canvas.fillText('Raps',area.x,ya);canvas.fillStyle=`rgba(240,241, 18, 0.7)`;}
      if(x==5){canvas.fillText('Löwenzahn',area.x,ya);canvas.fillStyle=`rgba(246,241,106, 0.7)`;}
      if(x==6){canvas.fillText('Robinie',area.x,ya);canvas.fillStyle=`rgba(106,246,176, 0.5)`;}
      if(x==7){canvas.fillText('Kastanie',area.x,ya);canvas.fillStyle=`rgba(128,  0,  0, 0.5)`;}
      if(x==8){canvas.fillText('Brombeere',area.x,ya);canvas.fillStyle=`rgba(111, 44,145, 0.5)`;}
      if(x==9){canvas.fillText('S.-Linde',area.x,ya);canvas.fillStyle=`rgba(40,180, 99, 0.5)`;}
      if(x==10){canvas.fillText('W.-Linde',area.x,ya);canvas.fillStyle=`rgba(40,180, 99, 0.7)`;}
      if(x==11){canvas.fillStyle=`rgba(243,156, 18, 0.2)`;}//orange
     canvas.fillRect(area.x, ya, area.w, yb);
     }
    }"?>
	var w=BL.xAxisRange();
	if((w[1]-w[0])> <?php $ww=$Underlay*86405000; echo $ww;?>){return;}
    var  lf,rg,tr,bl;
	var wx=w[0];
    <?php if($Underlay=="0")echo"return;";
    $rd=substr($Underlay_Col,0,2);
    $gn=substr($Underlay_Col,2,2);
    $bl=substr($Underlay_Col,4,2);
    echo 'canvas.fillStyle="rgba('.hexdec($rd).','.hexdec($gn).','.hexdec($bl).',0.5)";';
    $wtg=1000* 60*60*($Underlay_Ab - $Underlay_Mo);
    echo "var wtg=".$wtg.";";?>
	var datum=new Date();
	for(var i=0;i<BL.numRows();i++){datum.setTime(BL.rawData_[i][0]);if(datum.getHours()==<?php echo"$Underlay_Mo";?>){wx=BL.rawData_[i][0];break;}}
    for(;wx<w[1];wx+=86400000){
      bl=g.toDomCoords(wx,-20);tr=g.toDomCoords(wx+wtg,+20);lf=bl[0];rg=tr[0]-lf;
      canvas.fillRect(lf, area.y, rg, area.h);
    }
  },
  zoomCallback:function(a,b,c){if(!move){berechne_sum();}},
  <?php if($MultiType !=-1){?>
   pointClickCallback: function(event, p){
  if(p.annotation)return;//Checke, ob an der Stelle eine Anmerkung besteht
  BL.updateOptions({rollPeriod:1});//neu
  if(Werteloeschen==false){
    document.getElementById('AnmkForm').style.display="block";//Form für neue Anmerkung "einblenden"
    document.getElementById('LoeAenForm').style.display="none";//Form loschen oder ändern einer Anmerkung ausblenden
    document.getElementById('KonfigPasswortEingabeForm').style.display='none';
    document.getElementById('WertBtn').disabled=true;
    document.getElementById('AnmerkungenBtn').disabled=false;
    var anns=BL.annotations();
    var ann_num=anns.length;
    if(ann_num==ann_count){//letzte Anmerkung loschen - nur eine neue pro Speicherung erlaubt
      anns.splice(ann_num-1,1);
    }
    var datum=new Date(p.xval);
    var dat_str=String(datum.getFullYear())+ "/" + String("0" +(datum.getMonth()+1)).slice(-2)+ "/" + String('0'+datum.getDate()).slice(-2)+ " " + String('0'+datum.getHours()).slice(-2)+ ":" + String('0'+datum.getMinutes()).slice(-2)+ ":" + String('0'+datum.getSeconds()).slice(-2);
    var ann={series:p.name,xval:p.xval,shortText:"? Text",text:"<?php echo $SAs[126] ?>"};
    anns.push(ann);
    BL.setAnnotations(anns);
    document.getElementById('Sensor_anno').value=p.name;//Anmerkung Sensor
    document.getElementById('Datum_anno').value=dat_str;//Anmerkung Datum
    document.getElementById('Termin_anno').value=p.xval;//Anmerkung Zeitstempel
    document.getElementById('K_anno').value="<?php echo $SAs[101] ?>";//Anmerkung Kurztext
    document.getElementById('Edit_anno').value="<?php echo $SAs[133] ?>";//Anmerkung Beschreibung lang
  }//ifWerteloeschen
  else{
    document.getElementById('WertloeschenForm').style.display="block";//Form Wertloschen einblenden
    var datum=new Date(p.xval);
    var dat_str=String(datum.getFullYear())+"/"+String("0"+(datum.getMonth()+1)).slice(-2)+"/"+String('0'+datum.getDate()).slice(-2)+" "+String('0'+datum.getHours()).slice(-2)+":"+String('0'+datum.getMinutes()).slice(-2)+":"+String('0'+datum.getSeconds()).slice(-2);
    document.getElementById('Sensor_annoL').value=p.name;
    document.getElementById('Datum_annoL').value=dat_str;
    document.getElementById('WertL').value=p.yval;
    document.getElementById('Termin_annoL').value=p.xval;
    Werteloeschen=true;
  }//else
   },
  showRangeSelector:true,rangeSelectorHeight:30,width:200,height:250,
  labelsSeparateLines:true,labelsShowZeroValues:true,legendFormatter: mylefo,pointSize:3,
  <?php }
  if($Legende=="immer")echo"legend:'always',";
  else if($Legende=="folgend")echo"legend:'follow',";
  else echo"legend:'never',";
 if($mobilePhone==0)echo"interactionModel: Dygraph.defaultInteractionModel";
 else{
   if($chartMobile==1)echo"interactionModel: Dygraph.defaultInteractionModel";
   if($chartMobile==2)echo"interactionModel: Dygraph.nonInteractiveModel";
   if($chartMobile==3)echo"interactionModel: Dygraph.nonInteractiveTouch";
   if($chartMobile==4)echo"interactionModel: Dygraph.nonInteractiveTouchOnly";
   if($chartMobile==5)echo"interactionModel:{}";
  }
  ?>
});//new Ende

//*****************
BL.ready(function(){
window.addEventListener("resize",my_onresize);
window.addEventListener("mouseup",my_mouseup);
window.addEventListener("dblclick",my_mouseup);
my_onresize();
//Datei notes.csv nach Anmerkungen durchsuchen und im Array für die Darstellung aufbereiten-----
<?php
$anmerkungen=array();$b=0;
if(!file_exists($Csvdatei)){//StartbildschirmNote
  if($MultiType>=0){
  array_push($anmerkungen,$HelpArraySensoren[7*5]." ".$HelpArraySensoren[7*5+4]);//"Spannung Solarzelle";
  array_push($anmerkungen,"2022/10/28 00:00:00");//"2022-10-28"
  array_push($anmerkungen,"logger");
  array_push($anmerkungen,"Datenlogger für Imker");
  $b=4;
  }
}
else{
  $NotesFileName="";
  assignNotesfile(1);
  if(file_exists($NotesFileName)){
  $narray=file($NotesFileName);$ni=sizeof($narray);
  for($a=0;$a<$ni;$a++){
    $what=trim($narray[$a]);$x=explode(",",$what);$s=sizeof($x);
    if($s>1){
      $Sensorx=$x[0];
      $H_Sens=html_entity_decode($HelpArraySensoren[$Sensorx*5]).' '.html_entity_decode($HelpArraySensoren[$Sensorx*5+4]);
      if(is_numeric($Sensorx)){
        $Sensorx=$H_Sens;//html_entity_decode($HelpArraySensoren[$Sensorx*5]);
        $Anmerkung=html_entity_decode($x[$s-2]);$AktualisierungStamp=$x[$s-1];
        if($AktualisierungStamp>$ErstesDatum){
          $DatumAnmerkung=date("Y-m-d\TH:i:sP",$AktualisierungStamp);//eigen-utc-1: ISO 8601 mit Versatz, passend zur Datenzeile
          array_push($anmerkungen,$Sensorx);//Sensor im Array merken
          $b++;array_push($anmerkungen,$DatumAnmerkung);//Datumsstempel im Array merken
          $b++;$y=explode("&",$Anmerkung);array_push($anmerkungen,$y[0]);//Anmerkung kurz im Array merken
          $b++;array_push($anmerkungen,$y[1]);//Anmerkung lang im Array merken
          $b++;
    }}}
  }//ende for-schleife
}}//Ende Anmerkungen Array erstellen

echo"BL.setAnnotations([  ";
  for($w=0;$w < $b;$w++){
   echo"\n{"; echo"series: '".$anmerkungen[$w]."',";
   $w++;
   echo'xval: Date.parse(\''.$anmerkungen[$w].'\'),';
   $w++;
   if(!strpos($anmerkungen[$w],".png")===false)echo'icon: "'.$anmerkungen[$w].'", width: 30, height: 30';
   else echo'shortText: "'.$anmerkungen[$w].'", width: '.(6+8*strlen($anmerkungen[$w]));
   $w++; echo',text: "'.$anmerkungen[$w].'",';echo"},";
  }//for $w
echo"]);";
if($TageswertAnzeige!="false" &&($MultiType>=0)){
	echo"tageswertanwahl();\n";
	if($Summe !="false"){
		echo"setTimeout(function(){berechne_sum();},300);"."\n";
		$x=$HelpAnzahlSensoren+1;echo"document.getElementById('cb$x').checked=true;"."\n";
		$x++;echo"BL.setVisibility($x,true);"."\n";
	}
}
?>
var anns=BL.annotations();
ann_count=anns.length+1;
<?php echo "set_btn_and_curv(".$HelpAnzahlSensoren+2 .",1);";
if(isset($Zoom))if((int)$Zoom > 0)echo"zoom($Zoom * 3600);"."\n";?>
//setTimeout(function(){my_onresize();},50);
});//.ready ende

function my_mouseup(e){
if(Ax2Rng){let y=e.clientY;var rect=document.getElementById("BL_grafik").getBoundingClientRect();if(y>rect.top){Rng_Axes();}}}

function mylefo(data){//legend formatter
  if(data.x==null){return '<br>';}
  var d_a=new Date(data.x);var html=d_names[d_a.getDay()]+' '+data.xHTML;
  data.series.forEach(function(series){
    if(!series.isVisible)return;if(!series.yHTML)return;
    var labeledData=series.labelHTML+': '+ series.yHTML;
    if(series.isHighlighted){labeledData='<b>'+labeledData+'</b>';}
    html+='<br>'+series.dashHTML+' '+labeledData;
  });
return html;
}

//show_points: Datenpunkte zeigen
function show_points(){
if(points_show){BL.updateOptions({drawPoints:false});points_show=0;document.getElementById("123").style.backgroundColor="lightgrey";}
else{BL.updateOptions({drawPoints:true});points_show=1;document.getElementById("123").style.backgroundColor="green";}
}

//set_legend: Legende Varianten
<?php if($Legende=="immer")echo"var legend_state=1;";
    else if($Legende=="folgend")echo"var legend_state=2;";
        else echo"var legend_state=0;"; ?>
function set_legend(){
if(legend_state==2){document.getElementById("124").style.backgroundColor="lightgrey";BL.updateOptions({legend:'never'});legend_state=0;}
else if(legend_state==1){document.getElementById("124").style.backgroundColor="grey";BL.updateOptions({legend:'follow'});legend_state=2;}
else{document.getElementById("124").style.backgroundColor="green";BL.updateOptions({legend:'always'});legend_state=1;}
//animate();
}

//** Label fuer Achsen festlegen, valueRange
function setup_Axes(){
var y_lbl=0;y2_lbl=0;y_einh_lbl=0;y2_einh_lbl=0;
var curve_y=0,curve_y2=0,n;
var y_label="";
var y2_label="";
var y2Kurven=[<?php for($y=0;$y < $HelpAnzahlSensoren;$y++){ if(strpos($HelpArraySensoren[$y*5+3],"y2")> 0)echo"true,";else echo"false,";} if($TageswertAchse=="y2")echo"true,true,true";else echo"false,false,false";?>];//zeigt an welche Kurven auf y oder y2 achse liegen

var is_visible=BL.visibility();
for(var i=0;i<=<?php echo $HelpAnzahlSensoren+2; ?>;i++){
 if(is_visible[i]){
  if(y2Kurven[i]){curve_y2=i;n=y2_label.includes(EinzelEinheiten[i]);
	if(n==0){if(y2_label.length>1){y2_label+=(", ");}y2_label=y2_label+EinzelEinheiten[i];y2_einh_lbl++;
	}else y2_lbl++;;
  }else{curve_y=i;n=y_label.includes(EinzelEinheiten[i]);
	if(n==0){if(y_label.length>1){y_label+=(", ");}y_label=y_label+EinzelEinheiten[i];y_einh_lbl++;
	}else y_lbl++;
}}}

var ycol="black";
var y2col="black";
Ax2Rng=0;
BL.updateOptions({gridLineColor:"black"});
BL.updateOptions({axes:{y2:{gridLineColor:"black"}}});
if(y_einh_lbl==1){if(y_lbl)BL.updateOptions({ylabel:y_label});else BL.updateOptions({ylabel:EinzelSensoren[curve_y]+'  '+y_label});
}else if(y_einh_lbl>1){BL.updateOptions({ylabel:y_label});}
else if(y_einh_lbl==0){
    <?php if($mobilePhone==1)echo"ycol='ivory';BL.updateOptions({gridLineColor:'ivory'});";?>
	if(y2_einh_lbl==1){if(y2_label!=" "){<?php if($mobilePhone==0)echo'Ax2Rng=2;';?> BL.updateOptions({ylabel:'<?php echo $SAs[140]; ?>'+y2_label});}
    else{ BL.updateOptions({ylabel:" "});}}
	else{BL.updateOptions({ylabel:" "});BL.updateOptions({gridLineColor:"ivory"});ycol="ivory";}
}
//##############
if(y2_einh_lbl==1){if(y2_lbl)BL.updateOptions({y2label:y2_label});else BL.updateOptions({y2label:EinzelSensoren[curve_y2]+'  '+y2_label});
}else if(y2_einh_lbl>1){BL.updateOptions({y2label:y2_label});}
else if(y2_einh_lbl==0){
    <?php if($mobilePhone==1)echo"y2col='ivory';BL.updateOptions({axes:{y2:{gridLineColor:'ivory'}}});"?>
	if(y_einh_lbl==1){if(y_label!=" "){BL.updateOptions({y2label:'<?php echo $SAs[140]; ?>'+y_label});<?php if($mobilePhone==0)echo'Ax2Rng=1;';?>}
    else{ BL.updateOptions({y2label:" "});}}
	else{BL.updateOptions({y2label:" "});BL.updateOptions({axes:{y2:{gridLineColor:"ivory"}}});y2col="ivory";}
}
BL.updateOptions({axes:{y:{valueRange:[null,null]}}});BL.updateOptions({axes:{y2:{valueRange:[null,null]}}});
axCol(ycol,y2col);
Rng_Axes();
}//setup_axes

//valueRange fuer relative Achsen konfigurieren
function Rng_Axes(){
var rng_y;
var y_offset;
if(Ax2Rng==1){
  rng_y=BL.yAxisRange(0);
  y_offset=(rng_y[1]-rng_y[0])*0.1;if(Math.abs(rng_y[0])< 0.01)y_offset=0;rng_y[1]=rng_y[1]-rng_y[0]-y_offset;rng_y[0]=-y_offset;
  BL.updateOptions({axes:{y2:{valueRange:rng_y}}});
}else if(Ax2Rng==2){
  rng_y=BL.yAxisRange(1);
  y_offset=(rng_y[1]-rng_y[0])*0.1;if(Math.abs(rng_y[0])< 0.01){y_offset=0;}rng_y[1]=rng_y[1]-rng_y[0]-y_offset;rng_y[0]=-y_offset;
  BL.updateOptions({axes:{y:{valueRange:rng_y}}});
}
}//Rng_Axes

function axCol(ycol,y2col){
var sd=document.styleSheets[1].cssRules;
 for(const rule of sd){
  if(rule.type===CSSRule.STYLE_RULE){
	if(rule.selectorText==="#BL_grafik .dygraph-y2label"){ rule.style.color=y2col;}
	if(rule.selectorText==="#BL_grafik .dygraph-axis-label-y2"){rule.style.color=y2col;}
	if(rule.selectorText==="#BL_grafik .dygraph-ylabel"){rule.style.color=ycol;}
	if(rule.selectorText==="#BL_grafik .dygraph-axis-label-y1"){rule.style.color=ycol;}
 }}
}

//Kurve ein - ausblenden
function change(el){//handle event
  var btn_nmr=el.id;
  var box=parseInt(btn_nmr.substr(2,3));//id="cbxy"
  var check=el.checked;
  set_btn_and_curv(box,check);
}

//set buttons and curve
function set_btn_and_curv(box,check){
var e=document.getElementById("tagwertbox");
var Value;
var Nummer=6;
if(e.selectedIndex>=0){
 Value=e.options[e.selectedIndex].value; if(Value.length<=2){Nummer=parseFloat(Value);}
 if((Nummer==2)<?php if($MultiType <2)echo"||(Nummer==13)";elseif($MultiType >1)echo"||(Nummer==1)";?>){if(GTS==2)GTS=1;}
}
var v;
  <?php echo"if((!check)||(box==".($HelpAnzahlSensoren+2).")){";//aktiver Button macht Kurve an
    for($i=0;$i<$HelpAnzahlSensoren;$i++){echo"\n".'  v=document.getElementById("cb'.$i.'").checked; BL.setVisibility('.$i.', v);';}//for
    echo"\n".'  v=document.getElementById("cb'.$HelpAnzahlSensoren.'").checked;';
    echo' BL.setVisibility('.$HelpAnzahlSensoren.',v); BL.setVisibility('.($HelpAnzahlSensoren+1).',v);';
echo"\n".'  v=document.getElementById("cb'.($HelpAnzahlSensoren+1).'").checked;BL.setVisibility('.($HelpAnzahlSensoren+2).',v);'."}\n";
?>
else{
  if(box < <?php echo $HelpAnzahlSensoren; ?>){
<?php for($i=0;$i <=$HelpAnzahlSensoren+2;$i++){echo'  BL.setVisibility('.$i.', false);'."\n";}?>
  BL.setVisibility(box,true);
  if(GTS==1)GTS=2;
  }
}

if(e.selectedIndex>=0){
<?php if($MultiType>=0){?>
 Nummer--;
 var nmr="cb" + Nummer.toString();
 if(box==<?php echo $HelpAnzahlSensoren; ?>){//Tageswerte
  EinzelEinheiten[<?php echo $HelpAnzahlSensoren; ?>]=EinzelEinheiten[Nummer];
  EinzelEinheiten[<?php echo $HelpAnzahlSensoren+1; ?>]=EinzelEinheiten[Nummer];
  berechne_tag(Nummer+1);summe_setup=0;
  if(check){//Wert zur Tageskurve an
    document.getElementById(nmr).checked=true;//Button
    BL.setVisibility(Nummer,true);//Kurve
    BL.updateOptions({});
    document.getElementById('cb<?php echo $HelpAnzahlSensoren; ?>').checked=true;
    if(GTS==1){
      BL.setVisibility(<?php echo $HelpAnzahlSensoren+2; ?>,true);
      document.getElementById('cb<?php echo $HelpAnzahlSensoren+1; ?>').checked=true;
    }
  }else{
    BL.updateOptions({rollPeriod:roll_period});
  }
  BL.setVisibility(<?php echo$HelpAnzahlSensoren;?>,check);//Tw+
  BL.setVisibility(<?php echo$HelpAnzahlSensoren+1;?>,check);//Tw-
  if(document.getElementById('cb<?php echo $HelpAnzahlSensoren+1; ?>').checked){
   berechne_sum();summe_setup=1;
  }
 }else if(box==<?php echo $HelpAnzahlSensoren+1; ?>){//Button Summe
   EinzelEinheiten[<?php echo $HelpAnzahlSensoren+2; ?>]=EinzelEinheiten[Nummer];
   if(summe_setup==0){berechne_tag(Nummer+1);berechne_sum();summe_setup=1;}
   if(check){//Wert zur Tageskurve an
     document.getElementById(nmr).checked=true;//Button
     BL.setVisibility(Nummer,true);//Kurve
     BL.updateOptions({});
   }
   BL.setVisibility(<?php echo $HelpAnzahlSensoren+2; ?>,check);//Summe
 }
<?php } ?>
}
setup_Axes();
}//function change

//Box Tageswertanwahl
function tageswertanwahl(){
 var e=document.getElementById("tagwertbox");
 if(e.selectedIndex >=0){
  var Value=e.options[e.selectedIndex].value;
  var Nummer=6;
  if(Value.length <=2)Nummer=parseFloat(Value);
  EinzelEinheiten[<?php echo $HelpAnzahlSensoren; ?>]=EinzelEinheiten[Nummer-1];
  EinzelEinheiten[<?php echo $HelpAnzahlSensoren+1; ?>]=EinzelEinheiten[Nummer-1];
  EinzelEinheiten[<?php echo $HelpAnzahlSensoren+2; ?>]=EinzelEinheiten[Nummer-1];
  berechne_tag(Nummer);//force
  BL.updateOptions({});
  if(GTS==0){
    summe_setup=0;//Summe
    BL.setVisibility(<?php echo $HelpAnzahlSensoren+2; ?>,false);
    document.getElementById('cb<?php echo $HelpAnzahlSensoren+1; ?>').checked=false;
  }
  else{
    BL.setVisibility(<?php echo $HelpAnzahlSensoren+2; ?>,true);
    document.getElementById('cb<?php echo $HelpAnzahlSensoren+1; ?>').checked=true;
  }
  set_btn_and_curv(<?php echo $HelpAnzahlSensoren; ?>,true);//btn tageswert
  BL.updateOptions({});
 }
}

//Berechne Tageszunahme
function berechne_tag(Nummer){
if(typeof BL==='undefined'){return;}
if(typeof BL.rawData_==='undefined'){return;}
if(roll_period>8)BL.updateOptions({rollPeriod:8});
if(Nummer==0){if(tag_setup==1){return;}else{Nummer=6;}}
var k,i,hr_akt,tx_time;
var g_alt,g_neu;
var suche_tag=1,tageswert=0.0;
var old_d,cur_day,day,cur_month;
var df_k,diff_korr,g_korr;
var datum=new Date();
var boundary=BL.numRows();//maximale Anzahl Punkte
GTS=0;
data_d.length=0;
g_neu=BL.rawData_[0][Nummer];//Startwert Tageswert
if(g_neu===null){g_neu=0;}
datum.setTime(BL.rawData_[0][0]);
day=datum.getDate();
var x_ax=boundary-1;
if(Nummer==6){//Auswertung Gewicht
 var e=document.getElementById("tagwertbox");//hole Grenzwert
 var sum_grz=parseFloat(e.options[e.selectedIndex].value);
 for(i=0;i<boundary;i++){datum.setTime(BL.rawData_[i][0]);cur_day=datum.getDate();hr_akt=datum.getHours();
  if(suche_tag){suche_tag=0;k=i;if(k>0){k--;}diff_korr=0.0;g_korr=0.0;day=cur_day;
   while((day==cur_day)&&(k<x_ax)){
    if(BL.rawData_[k][6]!==null){
     if(BL.rawData_[k+1][6]===null){var ix=1;while(ix<10){ix++;if(BL.rawData_[k+ix][6]!==null){df_k=BL.rawData_[k][6]-BL.rawData_[k+ix][6];break;}}}
     else{df_k=BL.rawData_[k][6]-BL.rawData_[k+1][6];}
	 if(Math.abs(df_k)>sum_grz){g_korr+=df_k; }
	}k++;datum.setTime(BL.rawData_[k][0]);day=datum.getDate();
   }
   old_d=cur_day;g_alt=g_neu;if(BL.rawData_[k-1][6]!==null){g_neu=BL.rawData_[k-1][6];}else{g_neu=g_alt;}tageswert=g_neu-g_alt+diff_korr+g_korr;if(Math.abs(tageswert)<0.015)tageswert=0.0;
  }
  if(cur_day!=old_d){suche_tag=1;tageswert=0;}
  if((hr_akt>2)&&(hr_akt<23)){
   if(tageswert>0){data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>tageswert,<?php if($RollPeriod > 2)echo"0"?>,0]);}
   else if(tageswert<0){data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";}?><?php if($RollPeriod > 2)echo"0"?>,tageswert,0]);}
   else{data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>0,<?php if($RollPeriod > 2)echo"0"?>,0]);}
  }else{data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?><?php if($RollPeriod > 2)echo"0,0"; else echo","; ?>,0]);}
 }
}else if((Nummer==2)<?php if($MultiType <2)echo"||(Nummer==13)";elseif($MultiType >1)echo"||(Nummer==1)";?>){//Grünlandtemp
var g_temp=0;
var datapoints;
datum.setTime(BL.rawData_[0][0]);
 for(i=0;i<boundary;i++){datum.setTime(BL.rawData_[i][0]);cur_month=datum.getMonth();cur_day=datum.getDate();
     if((cur_month==0)&&(cur_day<5)){document.getElementById("Message_box").style.backgroundColor="#a9dfbf";document.getElementById("Message_box").textContent="<?php echo $SAs[149]; ?>";
       GTS=1;break;
 }}
 day=cur_day;
 for(i=0;i<boundary;i++){
  datum.setTime(BL.rawData_[i][0]);cur_month=datum.getMonth();
  if(cur_month < 6){//nur die ersten 5 Monate
    cur_day=datum.getDate();msg=1;
    datapoints=0;
    if(suche_tag){
      suche_tag=0;k=i;if(k>0){k--;}
      while((day==cur_day)&&(k<x_ax)){//whole day
        if(BL.rawData_[k][Nummer]!==null){
          tageswert+=BL.rawData_[k][Nummer];
          datapoints++;
        }
        k++;datum.setTime(BL.rawData_[k][0]);day=datum.getDate();
      }
      if(datapoints>0){
        tageswert=tageswert/datapoints;
        if(tageswert >0.0){if(cur_month==0)g_temp+=(tageswert*0.5);else if(cur_month==1)g_temp+=(tageswert*0.75);else g_temp+=tageswert;} else tageswert=0.0;
      }
    }
    if(cur_day!=day){suche_tag=1;cur_day=day;}
  }
   if(g_temp < 1500.0){data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>tageswert,,g_temp]);}
  else{data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>,,]);}
  tageswert=0.0;
}
 if(GTS==0){document.getElementById("Message_box").style.backgroundColor="#ffe4c4";document.getElementById("Message_box").textContent="<?php echo $SAs[149].$SAs[150]; ?>";}
}else{//Auswertung Regen//fuer alle Punkte//nur addieren
 for(i=0;i<boundary;i++){datum.setTime(BL.rawData_[i][0]);cur_day=datum.getDate();hr_akt=datum.getHours();
  if(suche_tag){suche_tag=0;k=i;if(k>0){k--;}tageswert=0;day=cur_day;
   while((day==cur_day)&&(k<x_ax)){//whole day
    if(BL.rawData_[k][Nummer]!==null){tageswert+=BL.rawData_[k][Nummer];}
     k++;datum.setTime(BL.rawData_[k][0]);day=datum.getDate();
    }
   old_d=cur_day;if(Math.abs(tageswert)<0.05)tageswert=0.0;
  }
  if(cur_day!=old_d){suche_tag=1;tageswert=0;}
  if((hr_akt>2)&&(hr_akt<=22)){
   if(tageswert>0){data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>tageswert,<?php if($RollPeriod > 2)echo"0"?>,0]);}
   else{data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?>0,<?php if($RollPeriod > 2)echo"0"?>,0]);}
  }else{data_d.push([new Date(BL.rawData_[i][0]),<?php for($a=1;$a<=$HelpAnzahlSensoren;$a++){echo"BL.rawData_[i][".$a."],";} ?><?php if($RollPeriod > 2)echo"0,0"; else echo","; ?>,0]);}
 }
}
BL.updateOptions({'file':data_d});//neue Werte laden
<?php if(($MultiType==0)&&($MultiType==1))echo"setTimeout(function(){berechne_sum();},10);"?>
tag_setup=1;
}

//Berechne Summe aktueller Anzeigebereich
function berechne_sum(){
if(typeof BL==='undefined'){return;}
if(typeof BL.rawData_==='undefined'){return;}
if(data_d.length==0){return;}//keine Daten
if(GTS>0)return;
var i=0,tim;
var datum=new Date();
var sum_gew=0,once=1;
var j=BL.numRows();//maximale Anzahl Punkte
for(x=0;x< <?php echo $HelpAnzahlSensoren+1; ?>;x++){//grenzen
  try{
    i=BL.boundaryIds_[x][0];//akueller Bereich
    j=BL.boundaryIds_[x][1];
    break;
  }catch(ignore){}
}
try{
for(;i<j;i++){
  datum.setTime(data_d[i][0]);tim=datum.getHours();
  if(once&&(tim>=4)&&(tim<18)){if(!isNaN(data_d[i+1][<?php echo $HelpAnzahlSensoren+1; ?>])){sum_gew=sum_gew+data_d[i+1][<?php echo $HelpAnzahlSensoren+1; ?>];once=0;}
  if(!isNaN(data_d[i+1][<?php echo $HelpAnzahlSensoren+2; ?>])){sum_gew=sum_gew+data_d[i+1][<?php echo $HelpAnzahlSensoren+2; ?>];once=0;}
  }else if((tim>=22)||(tim<4)){once=1;}
  data_d[i][<?php echo $HelpAnzahlSensoren+3; ?>]=sum_gew;
}//end for
}catch(ignore){}
BL.updateOptions({'file':data_d});
}

//Button Reset Zoom
function reset_Zoom(){zoomBtnColor();desired_range=null;BL.resetZoom();Rng_Axes();}

function zoomBtnColor(){
<?php
  echo'document.getElementById("nav8").style.backgroundColor="#D8D8D8";'."\n";
  echo'document.getElementById("nav24").style.backgroundColor="#BDBDBD";'."\n";
  if($Csvdatei[0]=='w'){//week: 1h, 2h, 4h, 8h, 24h, 1/2w,
   echo'document.getElementById("nav1").style.backgroundColor="#FAFAFA";'."\n";
   echo'document.getElementById("nav2").style.backgroundColor="#F2F2F2";'."\n";
   echo'document.getElementById("nav4").style.backgroundColor="#E6E6E6";'."\n";
   echo'document.getElementById("nav3d").style.backgroundColor="#A4A4A4";'."\n";
  }else{
   echo'document.getElementById("nav7d").style.backgroundColor="#BDBDBD";'."\n";
   if($Csvdatei[0]=='m'){//month: 2h, 4h, 8h,24h, 7d, 14d
    echo'document.getElementById("nav2").style.backgroundColor="#FAFAFA";'."\n";
    echo'document.getElementById("nav4").style.backgroundColor="#F2F2F2";'."\n";
    echo'document.getElementById("nav14d").style.backgroundColor="#A4A4A4";'."\n";
  }else{
    echo'document.getElementById("nav30d").style.backgroundColor="#D8D8D8";'."\n";
    echo'document.getElementById("nav90d").style.backgroundColor="#BDBDBD";'."\n";
    if($Csvdatei[0]=='b'){//gesamt: 2,4,8,24, week, 14 day, month, 3 month
      echo'document.getElementById("nav2").style.backgroundColor="#FAFAFA";'."\n";
      echo'document.getElementById("nav4").style.backgroundColor="#F2F2F2";'."\n";
      echo'document.getElementById("nav14d").style.backgroundColor="#A4A4A4";'."\n";
    }else if($Csvdatei[0]=='A'){//archiv:  8h, 24h , 7d, month, 3 month
  }}}
?>
}

//Button zeige(letzten)Tag/Monat/Woche usw
function zoom(res){
  zoomBtnColor();
  var x='x';
  if(res==3600)x="nav1";
  if(res==7200)x="nav2";
  if(res==14400)x="nav4";
  if(res==28800)x="nav8";
  if(res==86400)x="nav24";
  if(res==302400)x="nav3d";
  if(res==604800)x="nav7d";
  if(res==1209600)x="nav14d";
  if(document.getElementById(x))document.getElementById(x).style.backgroundColor="#a9dfbf";

  if(res>86400){BL.updateOptions({axes:{x:{pixelsPerLabel:90}}});}
  else{BL.updateOptions({axes:{x:{pixelsPerLabel:105}}});}
  var wold=BL.xAxisExtremes();
  var w=BL.xAxisRange();
  if((w[1]-res*1000)<wold[0]){w[0]=wold[0];//ganz links
    if((w[1]+res *1000)<wold[1]){w[1]=w[1]+res*1000;}//nach rechts geht noch
    else{w[1]=wold[1];}//ganz rechts
    desired_range=[w[0],w[1]];
  }else{desired_range=[w[1]-res*1000,w[1]];}
  animate();
}

//Button Ansicht nach links oder rechts verschieben
function pan(dir){
  var wold=BL.xAxisExtremes();
  var w=BL.xAxisRange();
  var scale=(w[1]-w[0]);//aktuelle X - Ansicht
  var amount=scale*dir;//Versatz
  if((dir<0)&&(w[0]>wold[0])){//Grenze links
    if((w[0]+amount)<=wold[0]){w[0]=wold[0]-amount;w[1]=w[0]+scale;}
    desired_range=[w[0]+amount,w[1]+amount];
    animate();
  }
  if((dir>0)&&(w[1]<wold[1])){//Grenze rechts
    if((w[1]+amount)>=wold[1]){w[1]=wold[1]-amount;w[0]=w[1]-scale;}
    desired_range=[w[0]+amount,w[1]+amount];
    animate();
  }
  animate();
}

//Button Zeige gleichen Bereich am rechten oder linkem Ende
function panend(dir){
  var wold=BL.xAxisExtremes();
  var w=BL.xAxisRange();
  var scale=(w[1]-w[0]);//Bereich aktuelle X - Ansicht
  var multiplier;
    if(dir<0){multiplier=(wold[0]-w[0])/scale;}
  else{multiplier=(wold[1]-w[1])/scale;}
  var amount=scale*multiplier;
  if((dir<0)&&(w[0]>wold[0])){//Grenze links erreicht?
    if((w[0]+amount)<=wold[0]){w[0]=wold[0]-amount;w[1]=w[0]+scale;}
    desired_range=[w[0]+amount,w[1]+amount];
    animate();
  }
  if((dir>0)&&(w[1]<wold[1])){//Grenze rechts erreicht ?
    if((w[1]+amount)>=wold[1]){w[1]=wold[1]-amount;w[0]=w[1]-scale;}
    desired_range=[w[0]+amount,w[1]+amount];
    animate();
  }
  animate();
}

function animate(){move++;setTimeout(function(){approach_range();},50);}

//Anzeigebereich festlegen
function approach_range(){
  if(!desired_range)return;
  if(move>=4){//(do not set another timeout.)
    BL.updateOptions({dateWindow:desired_range});
    berechne_sum();Rng_Axes();move=0;
  }else{//go halfway there
    var range=BL.xAxisRange();
    var new_range;
    new_range=[0.5*(desired_range[0]+range[0]),0.5*(desired_range[1]+range[1])];
    BL.updateOptions({dateWindow:new_range});
    animate();move++;
  }
}
<?php }//nicht konfig-Mode, dann grafik
echo"
</script>
<noscript><b>JavaScript must be enabled in order for you to use this page.</b>However, it seems JavaScript is either disabled or not supported by your browser. Enable JavaScript by changing your browser options, and then try again.
</noscript>
</body>
</html>";

function CSVbuilder($checktimes){//CSV Builder Version 4.0----
  $input="beelogger.csv";
  if(file_exists($input)==false)return;
  if($checktimes){ //no rebuild when date identical
	$ft=filemtime($input);
	$fw=$ft-1;if(file_exists("week.csv"))$fw=filemtime("week.csv");
	//echo ($fw -$ft)." ";
	if($fw >= $ft)return; // week neuer als beelogger
  }
  $array=file($input);
  $asize=sizeof($array);
  if($asize>0){
  while($asize--){
    $what=trim($array[$asize]);
    $x=explode(",",$what);
    $s=count($x);
    if($x[$s-1] !=''){//letzte Spalte=Zeitstempel abfragen
      $LastDate=(int)$x[$s-1];
      break;
    }
  }

//csv - Monat und Woche
   $L_m=$LastDate-2678400;//Monat etwa  60*60*24*31=2678400 Ticks
   $L_w=$LastDate-604800;//Woche etwa  60*60*24*7=604800 Ticks

   $fp_m=fOpen("month.csv", "w");
   $fp_w=fOpen("week.csv", "w");

   foreach($array as $val){
    $what=trim($val);
    $x=explode(",",$what);
    $s=count($x);//beelogger.csv Spalten pro Zeile
    if((int)$x[$s-1]>=$L_m)fputs($fp_m,$val);
    if((int)$x[$s-1]>=$L_w)fputs($fp_w,$val);
   }
  fclose($fp_w);
  fclose($fp_m);

  }//if$asize>0
}//Ende function csv-Builder 4.0
 ?>
