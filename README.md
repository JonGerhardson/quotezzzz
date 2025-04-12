# quotezzzz
GUI app to compare quotations to source material to verify their accuracy

Load (or paste) text you want to check into the Document pane, and then put whatever source material you need to check it against in the "Transcript" pane. Click "Find Quotes" and it will highlight any partial matches from the source material if they appear in "quotation marks" in the text in the document window. That's it. Pretty simple. I'm using it to verify correct attribution when working form long transcripts.

![Screenshot of the Quote Verifier desktop application GUI. It shows a three-pane layout. The top-left pane displays the loaded document text ('document.txt'). The bottom-left pane lists found quotes with speaker tags; one quote '[Speaker 6] ~ very challenging' is selected (highlighted blue) and has orange text indicating a low match. 'Flag Sel.' and 'Unflag Sel.' buttons are visible above this list. The right pane displays the transcript text ('transcript.txt'), with the corresponding low-match segment ('very challenging') highlighted in yellow/orange. The bottom area shows structured details for the selected quote, including Speaker 6, Low Match status, 75.0% ratio, and positions.](https://github.com/user-attachments/assets/81c6c198-a1a1-403c-8a56-6643096a8199)


## Usage

1.  Ensure you have Python 3 installed.

2.  Run the script using:
    ```bash
    python quote_checker.py
    ```


## License
Highly doubt this will ever even come up, but do whatever with it I don't care.
