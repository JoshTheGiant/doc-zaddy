; MeTTa Knowledge Base for Greetings
(= (has-greeting "hello") True)
(= (has-greeting "hi") True)
(= (has-greeting "hey") True)

(= (response $greeting)
   (if (has-greeting "hello")
       "Hello_from_MeTTa"
       (if (has-greeting "hi")
           "Hi_there!"
           (if (has-greeting "hey")
               "Hey_back!"
               "I'm learning..."))))