<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$user_message = $data["message"] ?? "";


$url = "http://localhost:5005/webhooks/rest/webhook";

$options = [
    "http" => [
        "header"  => "Content-Type: application/json",
        "method"  => "POST",
        "content" => json_encode([
            "sender" => "user",
            "message" => $user_message
        ]),
    ],
];

$context = stream_context_create($options);
$result = file_get_contents($url, false, $context);

if ($result === FALSE) {
    
    echo json_encode([
        "success" => false,
        "message" => "Error connecting to the chatbot API"
    ]);
} else {
    
    echo $result;
}
?>
