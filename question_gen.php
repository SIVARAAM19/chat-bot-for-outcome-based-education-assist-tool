<?php

$db_config = [
    'host' => 'localhost',
    'dbname' => 'oat',
    'username' => 'root',
    'password' => ''
];


$model_url = "http://localhost:11434/api/generate";

// Initialize response array
$response = ['success' => false, 'data' => null, 'error' => null];

try {
    
    $dsn = "mysql:host={$db_config['host']};dbname={$db_config['dbname']};charset=utf8mb4";
    $pdo = new PDO($dsn, $db_config['username'], $db_config['password']);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
    
        if (isset($input['custom_mode']) && $input['custom_mode']) {
            $text = trim($input['unit_text'] ?? '');
            $level = trim($input['knowledge_level'] ?? '');
            $twoMarks = intval($input['two_marks'] ?? 0);
            $fiveMarks = intval($input['five_marks'] ?? 0);
    
            if (empty($text) || empty($level) || ($twoMarks === 0 && $fiveMarks === 0)) {
                echo json_encode([
                    'success' => false,
                    'error' => 'Missing input fields for custom question generation.'
                ]);
                exit;
            }
    
            // You would ideally replace this logic with OpenAI or your question generation engine.
            // For now, let's simulate dummy questions.
    
            $questions = [];
    

$connection_test = @fsockopen("localhost", 11434, $errno, $errstr, 10);
if (!$connection_test) {
    throw new Exception('Ollama server is not running. Please start the Ollama service first. Error: ' . $errstr);
}
fclose($connection_test);

// Detect model
$model_to_use = 'tinyllama';
$model_check = curl_init("http://localhost:11434/api/tags");
curl_setopt($model_check, CURLOPT_RETURNTRANSFER, true);
$models_json = curl_exec($model_check);
curl_close($model_check);

if ($models_json) {
    $models = json_decode($models_json, true);
    if ($models && isset($models['models'])) {
        foreach ($models['models'] as $model) {
            if (isset($model['name']) && $model['name'] === 'tinyllama') {
                $model_to_use = 'tinyllama';
                break;
            }
        }
    }
}

for ($i = 0; $i < ($twoMarks + $fiveMarks); $i++) {
    $marks = ($i < $twoMarks) ? 2 : 5;
    $prompt = "You are an expert question setter for a university exam.\n\nGenerate 1 clear and relevant question from the following content:\n\n\"{$text}\"\n\nKnowledge Level: {$level}\nMarks: {$marks}\n\nGuidelines:\n- Use action words like Explain, Analyze, Describe, etc.\n- Do not include answer, instructions, or word count.\n- Avoid repetition, and make it unique.\n\nOnly return the question.";

    $ch = curl_init($model_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'model' => $model_to_use,
        'prompt' => $prompt,
        'stream' => false,
        'options' => [
            'temperature' => 0.9,
            'top_p' => 0.95,
            'num_predict' => 300,
            'seed' => rand(1, 9999)
        ]
    ]));

    $result = curl_exec($ch);
    curl_close($ch);

    $full_response = '';
    $lines = explode("\n", $result);
    foreach ($lines as $line) {
        if (empty(trim($line))) continue;
        $json_response = json_decode($line, true);
        if ($json_response && isset($json_response['response'])) {
            $full_response .= $json_response['response'];
        }
    }

    $questions[] = trim($full_response);
}
        }
    }
    
    
   
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $action = $_GET['action'] ?? '';

        switch ($action) {
            case 'get_courses':
                $stmt = $pdo->query('SELECT code, name FROM course ORDER BY code');
                $response['data'] = $stmt->fetchAll();
                $response['success'] = true;
                break;

            case 'get_cos':
                if (isset($_GET['course_code'])) {
                    $stmt = $pdo->prepare('
                        SELECT id, co_number 
                        FROM course_outcome 
                        WHERE course_id = ?
                        ORDER BY co_number
                    ');
                    $stmt->execute([$_GET['course_code']]);
                    $response['data'] = $stmt->fetchAll();
                    $response['success'] = true;
                }
                break;

            case 'get_units':
                if (isset($_GET['course_code'])) {
                    $stmt = $pdo->prepare('
                        SELECT id, unit_number, unit_description,
                        CONCAT("Unit ", unit_number, ": ", LEFT(unit_description, 50), "...") as unit_title
                        FROM unit_contents 
                        WHERE course_id = ?
                        ORDER BY unit_number
                    ');
                    $stmt->execute([$_GET['course_code']]);
                    $units = $stmt->fetchAll();
                    
                    $response['data'] = $units;
                    $response['success'] = true;
                } else {
                    $response['error'] = 'Course code not provided';
                }
                break;
        }
    }
    
    elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        
        if ($data) {
           
            $stmt = $pdo->prepare('
                SELECT 
                    c.name as course_name,
                    c.code as course_code,
                    u.unit_description,
                    u.unit_number,
                    co.co_number
                FROM unit_contents u
                JOIN course c ON c.code = u.course_id
                JOIN course_outcome co ON co.course_id = c.code AND co.id = ?
                WHERE u.id = ?
            ');
            $stmt->execute([$data['co'], $data['unit']]);
            $details = $stmt->fetch();

            if ($details) {
                
                $timestamp = time();
                
                
                $prompt = "You are a university exam question creator. Current timestamp: {$timestamp}

Generate 1 unique and creative question for:
Course: {$details['course_code']} - {$details['course_name']}
Unit: {$details['unit_number']} - {$details['unit_description']}
CO: {$details['co_number']}
Level: {$data['knowledge_level']}
Marks: {$data['marks']}

Requirements:
- Worth {$data['marks']} marks
- Tests {$data['knowledge_level']} level
- Start with 'Explain', 'Analyze', 'Discuss', 'Compare', 'Evaluate', or 'Describe'
- Be specific to the unit content
- Be different from previous questions
- Focus on a different aspect of the unit than usual
- ONLY provide the question itself
- NO instructions to students
- NO word count requirements
- NO additional context

Your response:";

              
                $ch = curl_init($model_url);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($ch, CURLOPT_POST, true);
                curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30); 
                curl_setopt($ch, CURLOPT_TIMEOUT, 120); 

                
                $connection_test = @fsockopen("localhost", 11434, $errno, $errstr, 10);
                if (!$connection_test) {
                    throw new Exception('Ollama server is not running. Please start the Ollama service first. Error: ' . $errstr);
                }
                fclose($connection_test);

                
                $model_check = curl_init("http://localhost:11434/api/tags");
                curl_setopt($model_check, CURLOPT_RETURNTRANSFER, true);
                $models_json = curl_exec($model_check);
                curl_close($model_check);
                
                $model_to_use = 'tinyllama';
                $model_found = false;
                
                if ($models_json) {
                    $models = json_decode($models_json, true);
                    if ($models && isset($models['models'])) {
                        foreach ($models['models'] as $model) {
                            if (isset($model['name']) && $model['name'] === 'tinyllama') {
                                $model_found = true;
                                break;
                            }
                        }
                    }
                }
                
                if (!$model_found) {
                    error_log("TinyLlama model not found, falling back to llama2");
                    $model_to_use = 'llama2';
                }

                error_log("Sending request to Ollama API using model: " . $model_to_use);
                
              
                if ($model_to_use === 'tinyllama') {
                    $request_data = [
                        'model' => $model_to_use,
                        'prompt' => $prompt,
                        'stream' => false,
                        'options' => [
                            'temperature' => 1.0, 
                            'top_p' => 0.95,
                            'num_predict' => 300, 
                            'seed' => rand(1, 10000) 
                        ]
                    ];
                } else {
                   
                    $request_data = [
                        'model' => $model_to_use,
                        'prompt' => $prompt,
                        'stream' => false,
                        'options' => [
                            'temperature' => 0.9, 
                            'top_p' => 0.95, 
                            'num_predict' => 500,
                            'seed' => rand(1, 10000) 
                        ]
                    ];
                }
                
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($request_data));

                // Enhanced error handling
                curl_setopt($ch, CURLOPT_VERBOSE, true);
                $verbose = fopen('php://temp', 'w+');
                curl_setopt($ch, CURLOPT_STDERR, $verbose);

                $result = curl_exec($ch);
                error_log("Received response from Ollama API");
                
                $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                
                if (curl_errno($ch)) {
                    $curl_error = curl_error($ch);
                    rewind($verbose);
                    $verboseLog = stream_get_contents($verbose);
                    
                    error_log("Curl Error: " . $curl_error);
                    error_log("Verbose Log: " . $verboseLog);
                    error_log("HTTP Code: " . $http_code);
                    
                    $error_message = "Connection Error: ";
                    if (strpos($curl_error, "Failed to connect") !== false) {
                        $error_message .= "Ollama server is not running. Please ensure Ollama is started and running on port 11434.";
                    } elseif (strpos($curl_error, "Operation timed out") !== false) {
                        $error_message .= "Request timed out. TinyLlama should be faster than larger models. Please check if your GPU has enough memory or try restarting Ollama.";
                    } else {
                        $error_message .= $curl_error;
                    }
                    
                    throw new Exception($error_message);
                }

                curl_close($ch);
                fclose($verbose);

                if ($http_code === 200) {
                    $lines = explode("\n", $result);
                    $full_response = '';
                    
                    foreach ($lines as $line) {
                        if (empty(trim($line))) continue;
                        
                        $json_response = json_decode($line, true);
                        if ($json_response && isset($json_response['response'])) {
                            $full_response .= $json_response['response'];
                        } elseif ($json_response && isset($json_response['error'])) {
                            throw new Exception('Ollama API Error: ' . $json_response['error']);
                        }
                    }
                    
                    if (!empty($full_response)) {
                       
                        $clean_response = trim($full_response);
                        
                        
                        $clean_response = preg_replace('/^(Questions?|Course|Unit|CO|Level|Marks).*?\n/im', '', $clean_response);
                        
                        
                        $clean_response = preg_replace('/\b(remember|note:|please note|hint:|tip:).*$/im', '', $clean_response);
                        $clean_response = preg_replace('/\b(word count|marks allocation|learning outcomes).*$/im', '', $clean_response);
                        $clean_response = preg_replace('/\b\d+-\d+ words\b.*$/i', '', $clean_response);
                        $clean_response = preg_replace('/\bin your answer,.*$/im', '', $clean_response);
                        $clean_response = preg_replace('/\byour (answer|response) should.*$/im', '', $clean_response);
                        
                        
                        $clean_response = preg_replace('/^Question:\s*/i', '', $clean_response);
                        
                        // Format the display response
                        $formatted_response = "Questions for {$details['course_code']} - {$details['course_name']}\n" .
                                           "Unit {$details['unit_number']}\n" .
                                           "CO{$details['co_number']}\n" .
                                           "Level: {$data['knowledge_level']}\n" .
                                           "({$data['marks']} marks)\n\n" . 
                                           $clean_response;
                        
                        $response['success'] = true;
                        $response['data'] = [
                            'question' => $formatted_response,
                            'raw_question' => $clean_response, // Add the clean question without metadata
                            'course' => "{$details['course_code']} - {$details['course_name']}",
                            'unit_number' => $details['unit_number'],
                            'unit_description' => $details['unit_description'], // Keep full description for reference if needed
                            'co' => $details['co_number'],
                            'marks' => $data['marks'],
                            'knowledge_level' => $data['knowledge_level']
                        ];
                    } else {
                        throw new Exception('Failed to generate valid questions');
                    }
                } else {
                    throw new Exception('Ollama API Error: Failed to generate questions (HTTP ' . $http_code . ')');
                }
            } else {
                throw new Exception('Unit not found');
            }
        } else {
            throw new Exception('Invalid request data');
        }
    }
} catch (Exception $e) {
    $response['error'] = $e->getMessage();
    $response['debug'] = [
        'trace' => $e->getTraceAsString(),
        'line' => $e->getLine(),
        'file' => $e->getFile(),
        'last_error' => error_get_last()
    ];
    error_log("Error in question_gen.php: " . $e->getMessage());
}


header('Content-Type: application/json');
echo json_encode($response); 