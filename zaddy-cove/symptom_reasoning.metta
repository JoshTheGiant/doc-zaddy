; MeTTa Knowledge Base for Symptom Triage
(= (has-symptom "fever") True)
(= (has-symptom "cough") True)
(= (has-symptom "headache") True)
(= (has-symptom "sore_throat") True)
(= (has-symptom "nausea") True)

(= (diagnosis $symptoms)
   (if (and (has-symptom "fever") (has-symptom "cough"))
       "Flu"
       (if (and (has-symptom "headache") (has-symptom "sore_throat"))
           "Migraine"
           (if (and (has-symptom "nausea") (has-symptom "fever"))
               "Gastroenteritis"
               "Unknown condition"))))