import json
from parser import parse_transaction

# From Day 1 real vendor interviews
day1_phrases = [
    "ሽንኩርት ሁለት ኪሎ በመቶ ብር ሸጥኩኝ",
    # add your other real Day 1 vendor phrases here
]

# From Day 4 transcription log (what Azure actually returned)
day4_transcriptions = [
    "200 ብር",
    "3000 ብር",
    "ቲማቲም",
    "ቡና",
    "ሽንኩርት 2 ኪሎ በመቶ ብር ሽጥኩ",
    "ቲማቲም ሦስት ኪሎ 200 ብር ሸጡኩ",
    "ቡና 1 ኪሎ 500 ብር ተሸጠ",
    "ድንች, 50 ኪሎ ገዛሁ",
    "ስኳር 10 ኪሎ ገዛሁ በ 200 ብር",
    "ለትራንስፖርት 40 ብር ከፍ አልኩ",
]

tricky_phrases = [
    "ሽንኩርት ሸጥኩ",
    "ቡና ሸጥኩ",
    "ቲማቲም ገዛሁ",
    "ወተት ገዛሁ ዛሬ",
    "ሁለት መቶ ብር ሸጠ",
    "ሶስት መቶ ብር ገዛሁ",
    "ለአበበ ሁለት መቶ ብር በዱቤ ሰጠሁ",
    "ሽንኩርት ለማርታ በዱቤ ሸጥኩ አንድ መቶ ብር",
    "ከበደ ሶስት መቶ ብር በዱቤ ወሰደ",
    "ትንሽ ገንዘብ ሸጥኩ",
    "ዛሬ ጥሩ ሽያጭ ነበረኝ",
    "ትንሽ ነገር ገዛሁ",
    "ሁለት ኪሎ በ 50 ብር ሽንኩርት ሸጥኩ",
    "3 ኪሎ ቡና በሶስት መቶ ብር ገዛሁ",
    "ቲማቲም 2 ኪሎ በሃያ ብር ሸጥኩ",
]

def run_batch(name, phrases):
    print(f"\n{'='*50}\n{name}\n{'='*50}")
    for phrase in phrases:
        result = parse_transaction(phrase)
        print(f"\nInput: {phrase}")
        print(json.dumps(result, ensure_ascii=False, indent=2))

run_batch("DAY 1 VENDOR PHRASES", day1_phrases)
run_batch("DAY 4 TRANSCRIPTIONS", day4_transcriptions)
run_batch("TRICKY PHRASES", tricky_phrases)
