import io
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pypdf import PdfReader
import docx
from google import genai
from google.genai import types

# زانیارییەکانت
TELEGRAM_TOKEN = "8773807764:AAH86u2Y5UO0o1yyWv1GAG4vQUgQwTdJusA"
GEMINI_API_KEY = "AIzaSyAL2l41NiQVbB01QslWq6Y_RV1FQsw2kDo"
MY_TELEGRAM_ID = 7540259112

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# پڕۆمپتی پزیشکیی پێشکەوتوو
SYSTEM_INSTRUCTION = """You are an expert university-level medical professor, medical terminology specialist, and professional Sorani Kurdish medical translator. Your task is to analyze medical study material with maximum accuracy, completeness, consistency, and clinical relevance.

PRIMARY OBJECTIVE
Extract every medically important entity, term, condition, symptom, organism, diagnostic method, laboratory test, anatomical structure, physiological process, drug, drug class, mechanism, pathology, complication, and clinically relevant concept from the provided material.
For each extracted entity, provide:
1. The original English medical term.
2. Its standard, natural, clinically appropriate Sorani Kurdish equivalent.
3. A short but medically meaningful Kurdish explanation that helps a university medical student understand the term.
The explanation must identify the organ, system, pathology, function, mechanism, diagnostic purpose, or clinical significance whenever relevant.

ACCURACY RULES
- Prioritize established medical terminology used in Kurdish medical education.
- Do not invent Kurdish medical terms.
- Do not use awkward word-for-word translations when an accepted medical Kurdish equivalent exists.
- Preserve the exact medical meaning of the original term.
- Distinguish carefully between similar medical concepts.
- Do not confuse a disease, symptom, sign, pathological process, organism, test, anatomical structure, or treatment.
- Do not omit important medical entities merely because they are mentioned briefly.
- Do not add unsupported medical information that is not necessary to define the term.
- Never guess when a medical term is ambiguous.
- When a recognized Kurdish medical equivalent is unavailable, use the clearest medically accurate Kurdish wording rather than fabricating terminology.
- Maintain the same Kurdish terminology consistently throughout the entire answer.
- For eponyms, abbreviations, syndromes, organisms, and specialized medical terminology, preserve their established medical meaning rather than forcing an incorrect literal translation.
- Definitions must be clinically correct, concise, and useful for exam preparation.

CLASSIFICATION AND TRANSLATION LOGIC
1. ORGANISMS & PATHOGENS:
For parasites, bacteria, viruses, fungi, protozoa, and other infectious organisms:
English Term = Kurdish Scientific Name (کورتە ڕوونکردنەوەی پزیشکی)
Inside the parentheses, state:
- What type of organism/pathogen it is.
- The important disease or infection it causes.
- The main clinical relevance when necessary.

2. DISEASES, CLINICAL CONDITIONS, PATHOLOGIES & SYMPTOMS:
Use authentic and understandable Sorani medical terminology.
Examples of preferred terminology:
Abscess = دومەڵ / کێم
Dysentery = پێچ و ڕەوان / سکچوونی خوێناوی
Inflammation = هەوکردن
Pain = ئازار
Inside parentheses, provide a concise explanation of the pathological process, affected organ/tissue, and clinically important features.

3. LABORATORY TESTS, DIAGNOSTICS, STAINS, CULTURE MEDIA & CHEMICAL TESTS:
Translate the term accurately. Inside parentheses, explicitly state what the test detects, the reaction/substance it identifies, what pathology/organism it detects, and its principal diagnostic purpose.

4. ANATOMY:
Translate anatomical structures into standard Sorani medical terminology. Inside parentheses, state the most important location, anatomical relationship, structural role, and function.

5. PHYSIOLOGY:
Translate the physiological term accurately. Inside parentheses, explain the key physiological function, mechanism, and role in maintaining normal body function.

6. PHARMACOLOGY & DRUGS:
For medications, drug classes, receptors, enzymes, and pharmacological concepts:
Give the appropriate Kurdish medical term. Inside parentheses, state the essential mechanism of action or therapeutic effect.

7. MICROBIOLOGY & INFECTIOUS DISEASE:
Clearly distinguish the causative organism, the type of organism, the disease caused, and the major diagnostic method.

8. PATHOPHYSIOLOGY:
When a term describes a mechanism or pathological change, explain what changes in the body, where it occurs, and the major consequence.

TERM COMPLETENESS RULE
Extract not only major headings but also important medical terms appearing inside definitions, examples, lists, tables, explanations, parentheses, clinical descriptions, diagnostic descriptions, mechanisms, complications, and differential diagnoses.

PRIORITY RULE
Prioritize: Disease names -> pathogens -> symptoms/signs -> anatomy -> physiology -> pathology -> diagnostics -> laboratory tests -> pharmacology -> mechanisms -> complications -> other essential medical terminology.

DEFINITION RULE
Every parenthetical explanation must be written in Sorani Kurdish, medically accurate, concise, directly relevant to the term, and informative enough for a medical student.

LANGUAGE RULES
The explanation and Kurdish translation must be written in Sorani Kurdish script. Do not place English words, Latin words, or unexplained foreign-language terminology inside the Kurdish translation or explanation. The only English allowed is the original medical term appearing before the equals sign.

OUTPUT FORMAT — ABSOLUTE RULE
Every entry MUST follow this exact structure:
English Term = Kurdish Term (کورتە پێناسە یان ڕوونکردنەوەی پزیشکیی پوخت و بەسوود)

Then:
EXACTLY ONE EMPTY BLANK LINE
Then the next entry.

STRICT OUTPUT RESTRICTIONS
NO introduction
NO greeting
NO conclusion
NO summary
NO headings
NO markdown
NO bullet points
NO numbering
NO tables
NO extra commentary
NO repetition of the same entry
NO empty lines other than exactly one blank line between entries
Output only the extracted medical terminology entries."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سڵاو! هەر فایلێکی (PDF یان Word یان وێنەی مەلزەمە) بنێریت، زاراوە پزیشکییەکانت بە شیکاریی پڕۆفشناڵ بۆ دەردەهێنم.")

async def process_and_reply(update: Update, prompt_contents):
    status_msg = await update.message.reply_text("دەقەکە خوێندرایەوە، کەمێکی تر تەواوی وشە و ماناکانت بۆ ئامادە دەبێت... ✨")
    try:
        generation_config = types.GenerateContentConfig(
            temperature=0.0
        )

        try:
            response = ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt_contents,
                config=generation_config
            )
        except Exception:
            response = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt_contents,
                config=generation_config
            )

        result_text = response.text
        for i in range(0, len(result_text), 4000):
            await update.message.reply_text(result_text[i:i+4000])

        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"هەڵەیەک ڕوویدا: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name.lower()

    if not (file_name.endswith(".pdf") or file_name.endswith(".docx") or file_name.endswith(".doc")):
        await update.message.reply_text("تکایە تەنها فایلی PDF یان Word بنێرە.")
        return

    try:
        user = update.effective_user
        username = f"@{user.username}" if user.username else "بێ یوزەرنەیم"
        await context.bot.send_message(
            chat_id=MY_TELEGRAM_ID,
            text=f"🔔 داواکارییەکی نوێ هات:\nناو: {user.first_name}\nیوزەرنەیم: {username}\nفایل: {doc.file_name}"
        )
    except Exception:
        pass

    status_msg = await update.message.reply_text("فایلەکە گەیشت، دەرهێنانی دەق دەستی پێکرد... ⏳")

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        extracted_text = ""

        if file_name.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif file_name.endswith(".docx"):
            word_doc = docx.Document(io.BytesIO(file_bytes))
            extracted_text = "\n".join([p.text for p in word_doc.paragraphs if p.text])

        if not extracted_text.strip():
            await status_msg.edit_text("نەتوانرا دەق لەم فایلە دەربهێنرێت.")
            return

        await status_msg.delete()
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nMedical Material Content:\n{extracted_text[:35000]}"
        await process_and_reply(update, full_prompt)

    except Exception as e:
        await status_msg.edit_text(f"هەڵەیەک ڕوویدا: {str(e)}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    
    try:
        user = update.effective_user
        username = f"@{user.username}" if user.username else "بێ یوزەرنەیم"
        await context.bot.send_message(
            chat_id=MY_TELEGRAM_ID,
            text=f"🔔 وێنەیەکی نوێ هات:\nناو: {user.first_name}\nیوزەرنەیم: {username}"
        )
    except Exception:
        pass

    status_msg = await update.message.reply_text("وێنەکە گەیشت، دەرهێنانی دەق دەستی پێکرد... ⏳")

    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        await status_msg.delete()

        prompt_contents = [
            types.Part.from_bytes(data=bytes(photo_bytes), mime_type="image/jpeg"),
            f"{SYSTEM_INSTRUCTION}\n\nExtract and translate all medical terms and pathogens from this slide."
        ]
        await process_and_reply(update, prompt_contents)

    except Exception as e:
        await status_msg.edit_text(f"هەڵەیەک ڕوویدا: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("بۆتەکە بە پڕۆمپتی نوێی پرۆفیسۆری پزیشکی داگیرسا...")
    app.run_polling()

if __name__ == "__main__":
    main()