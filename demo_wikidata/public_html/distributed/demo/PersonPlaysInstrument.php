<?PHP

error_reporting(E_ERROR|E_CORE_ERROR|E_ALL|E_COMPILE_ERROR);
ini_set('display_errors', 1);

header('Content-type: application/json');

$callback = $_REQUEST['callback'] ;
$out = array () ;


session_start();

if (!isset($_SESSION['n'])) {
    $_SESSION['n'] = 1; // Initialize $n if not set
}


if ( $_REQUEST['action'] == 'desc' ) {

	$out = array (
		"label" => array ( "en" => "Musical Instruments Played by Artists" ) ,
		"description" => array ( "en" => "This game will show entities of artists in the musical field and the musical instruments played by them provided by GPT-3.5-Turbo." ) ,
		"icon" => 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Inkscape_vectorisation_test.svg/120px-Inkscape_vectorisation_test.svg.png'
	) ;

} else if ( $_REQUEST['action'] == 'tiles' ) {	



	// GET parameters
	$num = $_REQUEST['num'] ; // Number of games to return
	$lang = $_REQUEST['lang'] ; // The language to use, with 'en' as fallback; ignored in this game

	$out['tiles'] = array();
	for ( $i = 0 ; $i < $num ; $i++ ) {
		$n = $_SESSION['n']++;
		$g = array(
			'id' => rand(),
			'sections' => array () ,
			'controls' => array ()
		) ;
		// GET Tiles from Python
		$instruction = "python PythonApp/main.py -mt gpt -m gpt-3.5-turbo -r PersonPlaysInstrument -d val -p question -fs True -ex False -mn True -c " . strval($n);
		$python_output = exec($instruction);

		if ($python_output == "False") {
			$out['status'] = 'No more tiles!' ;
		}
		else {
			$output_array = explode(" ", $python_output);
			$len_output = count($output_array);
			
			$g['sections'][] = array ( 
				'type' => 'item' , 'q' => strval($output_array[0])
			) ;

			$accept_array = array(); // TODO: Connection with IDs
			for ($o = 2; $o < $len_output; $o++ ) {
				$accept_array[] = array ( 'type' => 'green' , 'decision' => 'yes' , 'label' => $output_array[$o]);
			}
			$g['controls'][] = array ( // TODO: Connection with API to edit
				'type' => 'buttons' ,
				'entries' => array_merge (
					$accept_array ,
					array(
						array ( 'type' => 'yellow' , 'decision' => 'yes' , 'label' => 'All previous options are correct' ) ,
						array ( 'type' => 'white' , 'decision' => 'skip' , 'label' => 'Skip' ) ,
						array ( 'type' => 'blue' , 'decision' => 'no' , 'label' => 'No option is correct' )
					)
				)
			) ;
			$out['tiles'][] = $g;
		}

	}
	
} else if ( $_REQUEST['action'] == 'log_action' ) {

	$out['status'] = 'Whatevaz, man' ;

} else {
	$out['error'] = "No valid action!" ;
}

print $callback . '(' ;
print json_encode ( $out ) ;
print ")\n" ;

?>
