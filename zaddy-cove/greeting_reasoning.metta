; MeTTa Knowledge Base for Greetings
(: has-greeting (-> String Bool))
(= (has-greeting "hello") True)
(= (has-greeting "hi") True)
(= (has-greeting "hey") True)

(: response (-> String String))
(= (response $greeting)
   (if (has-greeting $greeting)
       (case $greeting
         ("hello" "Hello_from_MeTTa")
         ("hi" "Hi_there!")
         ("hey" "Hey_back!")
         (_ "I'm learning..."))
       "I'm learning..."))