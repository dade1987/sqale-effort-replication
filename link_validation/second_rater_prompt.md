# Second link rater: model and instruction

Model: ChatGPT, GPT-6 Thinking (gpt-6-thinking), reasoning level "Extended" (OpenAI). Run by the authors on the two validation samples (50 MariaDB/Moodle issues, 50 Percona issues), provided as an Excel file.

## Original instruction (Italian, verbatim)

Revisiona i collegamenti issue → commit presenti nel file allegato.

Per ogni riga, apri la issue originale e analizza i commit associati, confrontando i diff effettivi con il problema descritto.

Assegna uno dei seguenti giudizi:

corretto = tutti i commit collegati rappresentano lavoro effettivamente svolto per quella issue.

parziale = almeno un commit è pertinente, ma sono presenti commit estranei oppure manca una parte evidente della correzione.

sbagliato = nessuno dei commit collegati rappresenta il lavoro svolto per quella issue.

Non basarti soltanto sui titoli delle issue o sui messaggi dei commit. Verifica il codice modificato, i test e la relazione tecnica con il problema.

Un commit può risolvere più issue senza essere necessariamente estraneo. Anche test, fixup, migrazioni e modifiche accessorie possono essere pertinenti.

Le righe sono in ordine casuale. Effettua una valutazione indipendente, senza conoscere o cercare i giudizi di altri revisori.

In caso di incertezza, segnala il dubbio senza inventare conclusioni.

Compila la colonna Giudizio e aggiungi brevi motivazioni nei casi dubbi.

Mantieni invariati dati, ordine delle righe e struttura originale del file Excel.

Al termine restituisci il file Excel compilato, pronto per calcolare l'accordo tra revisori.

## English translation

Review the issue → commit links in the attached file.

For each row, open the original issue and analyse the associated commits, comparing the actual diffs with the problem described.

Assign one of the following judgements:

correct = all linked commits represent work actually done for that issue.

partial = at least one commit is relevant, but there are unrelated commits or an evident part of the fix is missing.

wrong = none of the linked commits represents the work done for that issue.

Do not rely only on issue titles or commit messages. Check the changed code, the tests and the technical relation to the problem.

A commit can resolve several issues without necessarily being unrelated. Tests, fixups, migrations and ancillary changes can also be relevant.

The rows are in random order. Make an independent assessment, without knowing or looking for the judgements of other raters.

In case of uncertainty, report the doubt without inventing conclusions.

Fill in the Judgement column and add short reasons in doubtful cases.

Keep the data, row order and original structure of the Excel file unchanged.

At the end, return the completed Excel file, ready for computing inter-rater agreement.
