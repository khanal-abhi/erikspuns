<?

function pg_connection_string()
{

}

$db = pg_connect(pg_connection_string());
if (!$db)
{
	echo "Database connection error.";
	exit;
}

$query = "SELECT * FROM `users`";

$result = pg_query($db, $query);

?>