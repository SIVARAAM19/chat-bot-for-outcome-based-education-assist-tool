<?php

$db_config = [
    'host' => 'localhost',
    'dbname' => 'oat',
    'username' => 'root',
    'password' => ''
];

$model_url = "http://localhost:11434/api/generate";
$response = ['success' => false, 'data' => null, 'error' => null];

try {
    $dsn = "mysql:host={$db_config['host']};dbname={$db_config['dbname']};charset=utf8mb4";
    $pdo = new PDO($dsn, $db_config['username'], $db_config['password']);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);

        // CUSTOM MODE (free text + LLM)
        if (isset($input['custom_mode']) && $input['custom_mode']) {
            $text = trim($input['unit_text'] ?? '');
            $marks = $input['marks'] ?? [];
            $levels = $input['knowledge_levels'] ?? [];
        
            if (empty($text) || count($marks) === 0 || count($levels) === 0 || count($marks) !== count($levels)) {
                echo json_encode([
                    'success' => false,
                    'error' => 'Invalid question settings'
                ]);
                exit;
            }
        
            // ✅ Ollama setup
            $connection_test = @fsockopen("localhost", 11434, $errno, $errstr, 10);
            if (!$connection_test) {
                throw new Exception('Ollama server is not running. Please start the Ollama service. Error: ' . $errstr);
            }
            fclose($connection_test);
        
            $model_to_use = 'mistral';
            $model_check = curl_init("http://localhost:11434/api/tags");
            curl_setopt($model_check, CURLOPT_RETURNTRANSFER, true);
            $models_json = curl_exec($model_check);
            curl_close($model_check);
        
            if ($models_json) {
                $models = json_decode($models_json, true);
                if ($models && isset($models['models'])) {
                    $found = false;
                    foreach ($models['models'] as $model) {
                        if ($model['name'] === 'mistral') {
                            $found = true;
                            break;
                        }
                    }
                }
            }
        
            $questions = [];
        
            for ($i = 0; $i < count($marks); $i++) {
                $mark = intval($marks[$i]);
                $level = trim($levels[$i]);
                $previous_questions = implode("\n", $questions);

                $prompt = "You are an expert university-level question setter for Computer science.

                    Given the following content:
                    \"\"\"{$text}\"\"\"

                    Previously generated questions:
                    \"\"\"{$previous_questions}\"\"\"

                    Now, generate ONE new question based on a *different topic not already covered* above.

                    Generate ONE clear, short (max 2 lines) and specific question.

                    Instructions:
                    - Focus on a *different topic* from previous questions
                    - Target Bloom’s Level: {$level}
                    - Marks: {$mark}
                    - Return only a single concise question — no extra text
                    - Use appropriate verbs: 
                    - if {$level} = Remember: then use (List, Define, Identify)
                    - if {$level} = Understand: then use (Explain, Summarize, Describe)
                    - if {$level} = Apply: then use (Demonstrate, Illustrate)
                    - if {$level} = Analyze: then use (Compare, Differentiate, Analyze)
                    - if {$level} = Evaluate: then use (Assess, Critique, Justify)
                    - if {$level} = Create: then use (Design, Formulate, Build)

                    Constraints:
                    - Do NOT return answers or multi-sentence explanations
                    - No repetition of given words
                    - Limit the question to *a maximum of 20 words*
                    - Be specific, technical, and exam-ready

                    Output only the question text.";
        
                    $ch = curl_init($model_url);
                    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                    curl_setopt($ch, CURLOPT_POST, true);
                    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
                        'model' => $model_to_use,
                        'prompt' => $prompt,
                        'stream' => false,
                        'options' => [
                            'temperature' => 0.7,
                            'top_p' => 0.95,
                            'num_predict' => 150,
                            'seed' => rand(1, 9999)
                        ]
                    ]));
                    
                    $result = curl_exec($ch);
                    curl_close($ch);
                    
                    // Extract the response
                    $full_response = '';
                    $lines = explode("\n", $result);
                    foreach ($lines as $line) {
                        if (empty(trim($line))) continue;
                        $json_response = json_decode($line, true);
                        if ($json_response && isset($json_response['response'])) {
                            $full_response .= $json_response['response'];
                        }
                    }
                    
                    // Now apply word limit enforcement
                    $cleaned = trim($full_response);
                    $word_limit = 20;
                    $words = explode(' ', $cleaned);
                    if (count($words) > $word_limit) {
                        $cleaned = implode(' ', array_slice($words, 0, $word_limit)) .'?';
                    }
                    
                    // Append to final output
                    $questions[] = "[{$mark}M | {$level}] " . $cleaned;                    
            }
        
            echo json_encode([
                'success' => true,
                'questions' => $questions
            ]);
            exit;
        }
        

        // Your existing unit-based logic continues below...
        // No change to the remaining POST logic for course/unit/CO-based generation
    }

    // GET HANDLERS
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
                    $stmt = $pdo->prepare('SELECT id, co_number FROM course_outcome WHERE course_id = ? ORDER BY co_number');
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
                        WHERE course_id = ? ORDER BY unit_number
                    ');
                    $stmt->execute([$_GET['course_code']]);
                    $response['data'] = $stmt->fetchAll();
                    $response['success'] = true;
                } else {
                    $response['error'] = 'Course code not provided';
                }
                break;
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
