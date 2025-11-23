!(bind &self &self)

!(add-atom &self (= (symptom fever) True))
!(add-atom &self (= (symptom cough) True))
!(add-atom &self (= (symptom fatigue) True))
!(add-atom &self (= (symptom headache) True))

!(add-atom &self (=> (and (symptom fever) (symptom cough)) (disease flu)))
!(add-atom &self (=> (and (symptom fever) (symptom headache)) (disease malaria)))

!(add-atom &self (= (treatment flu) "Take rest and fluids"))
!(add-atom &self (= (treatment malaria) "Administer antimalarial drugs"))
