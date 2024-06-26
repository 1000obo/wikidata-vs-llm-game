<html>
    <body>
<?php
    $PlayerID = $_REQUEST['playerID'];
    $EntityID = $_REQUEST['entityID'];
    $Question = $_REQUEST['question'];
    $Answer = $_REQUEST['answer'];
    $Choice = $_REQUEST['choice'];
    try
    {
        $host = "db.ist.utl.pt";
        $user ="ist424817";
        $password = "kukv2488";
        $dbname = $user;
        $db = new PDO("pgsql:host=$host;dbname=$dbname", $user, $password);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $db->beginTransaction();

        $sql = "INSERT INTO llm_wikidata_study VALUES ('$PlayerID', '$EntityID', '$Question', '$Answer', '$Choice');";

        echo("<p>$sql</p>");

        $result = $db->prepare($sql);
        $result->execute();
        
        $db->query("commit;");

        $db = null;
    }
    catch (PDOException $e)
    {
        if ($db) {
            $db->query("rollback;");
        }
        echo("<p>ERROR: {$e->getMessage()}</p>");
    }
?>
    </body>
</html>
