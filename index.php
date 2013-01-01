<?

function pg_connection_string()
{
	return "host=ec2-54-243-230-119.compute-1.amazonaws.com port=5432 dbname=d1bpcicqqckeef user=nldgwtgemzohlw password=gETRu_wde0XQGyoW7GA-I4gNfF sslmode=require options='--client_encoding=UTF8'";

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