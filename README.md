# quotezzzz
GUI app to compare quotations to source material to verify their accuracy

Load two txt files, or paste into the windows tow texts, and click "Find Quotes" and it looks for any string of words that appear between "quotation marks" in the left pane, and shows you where they are in the text you load on the right. I'm using it to verify correct attribution when working form long transcripts. It looks like it's from the 1990s but it's easier than doing CTRL+F a million times. 


![Screenshot of the Quote Verifier desktop application GUI. It shows a three-pane layout. The top-left pane displays the loaded document text ('document.txt'). The bottom-left pane lists found quotes with speaker tags; one quote '[Speaker 6] ~ very challenging' is selected (highlighted blue) and has orange text indicating a low match. 'Flag Sel.' and 'Unflag Sel.' buttons are visible above this list. The right pane displays the transcript text ('transcript.txt'), with the corresponding low-match segment ('very challenging') highlighted in yellow/orange. The bottom area shows structured details for the selected quote, including Speaker 6, Low Match status, 75.0% ratio, and positions.](https://github.com/user-attachments/assets/81c6c198-a1a1-403c-8a56-6643096a8199)


## Usage

1.  Ensure you have Python 3 installed.

2.  Run the script using:
    ```bash
    python quote_checker.py
    ```
3.  The GUI window should appear.
4.  Use the "Load Document..." and "Load Transcript..." buttons or paste text directly into the respective panes.
5.  Optionally toggle the "Identify Speaker" checkbox.
6.  Click "Find Quotes & Matches" to process the texts.
7. Select quotes from the "Found Quotes" list to view details and highlights.
8. Use the "Flag Sel. (*)" / "Unflag Sel." buttons to mark quotes for review.


## License
Highly doubt this will ever even come up, but do whatever with it I don't care. 
