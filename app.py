import streamlit as st
import PyPDF2
import librosa
import soundfile as sf
import numpy as np
import tempfile
import os

from gtts import gTTS
from langdetect import detect


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF2Voice",
    page_icon="🔊",
    layout="centered"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🔊 PDF2Voice</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Convert PDF text into a single audio file'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "language" not in st.session_state:
    st.session_state.language = None


# ============================================================
# PDF UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📄 PDF Upload",
    type=["pdf"]
)


if uploaded_file is not None:

    st.session_state.pdf_file = uploaded_file

    st.success(
        f"✅ Uploaded: {uploaded_file.name}"
    )


# ============================================================
# BUTTON LAYOUT
# ============================================================

col1, col2, col3 = st.columns(3)


# ============================================================
# COLUMN 1
# ============================================================

with col1:

    if uploaded_file is not None:

        st.write("📄 PDF Ready")

    else:

        st.write("📄 Upload PDF")


# ============================================================
# COLUMN 2 - GENERATE AUDIO
# ============================================================

with col2:

    generate_clicked = st.button(
        "🎙️ Generate Audio",
        use_container_width=True
    )


# ============================================================
# GENERATE AUDIO
# ============================================================

if generate_clicked:

    if st.session_state.pdf_file is None:

        st.warning(
            "⚠️ Please upload a PDF first."
        )

    else:

        @st.dialog("🎙️ Generate Audio")
        def generate_audio_dialog():

            st.write(
                "Processing your PDF..."
            )

            progress = st.progress(0)

            status_text = st.empty()

            try:

                # =================================================
                # STEP 1 - READ PDF
                # =================================================

                status_text.write(
                    "📄 Reading PDF..."
                )

                pdf_bytes = (
                    st.session_state.pdf_file
                    .getvalue()
                )

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                ) as temp_pdf:

                    temp_pdf.write(pdf_bytes)

                    pdf_path = temp_pdf.name


                progress.progress(10)


                # =================================================
                # STEP 2 - EXTRACT TEXT
                # =================================================

                status_text.write(
                    "📖 Extracting text from PDF..."
                )

                with open(
                    pdf_path,
                    "rb"
                ) as pdf_file:

                    reader = PyPDF2.PdfReader(
                        pdf_file
                    )

                    full_text = ""

                    for page in reader.pages:

                        text = page.extract_text()

                        if text:

                            full_text += (
                                text + " "
                            )


                full_text = full_text.strip()


                if not full_text:

                    st.error(
                        "❌ No readable text found in the PDF."
                    )

                    os.remove(pdf_path)

                    return


                progress.progress(30)


                # =================================================
                # STEP 3 - LANGUAGE DETECTION
                # =================================================

                status_text.write(
                    "🌐 Detecting language..."
                )

                try:

                    detected_language = detect(
                        full_text[:1000]
                    )

                except Exception:

                    detected_language = "en"


                st.session_state.language = (
                    detected_language
                )


                st.info(
                    f"🌐 Detected Language: "
                    f"`{detected_language}`"
                )


                progress.progress(40)


                # =================================================
                # STEP 4 - SPLIT TEXT
                # =================================================

                status_text.write(
                    "✂️ Dividing text into sections..."
                )

                part1 = full_text[0:1000]

                part2 = full_text[1000:2000]

                part3 = full_text[2000:3000]


                # Check whether the PDF has enough text

                if not part1:

                    st.error(
                        "❌ PDF does not contain readable text."
                    )

                    os.remove(pdf_path)

                    return


                progress.progress(45)


                # =================================================
                # STEP 5 - TEMPORARY AUDIO FILES
                # =================================================

                temp_dir = tempfile.gettempdir()

                audio1_path = os.path.join(
                    temp_dir,
                    "pdf2voice_part1.mp3"
                )

                audio2_path = os.path.join(
                    temp_dir,
                    "pdf2voice_part2.mp3"
                )

                audio3_path = os.path.join(
                    temp_dir,
                    "pdf2voice_part3.mp3"
                )


                # =================================================
                # STEP 6 - TEXT TO SPEECH
                # =================================================

                status_text.write(
                    "🔊 Converting text to speech..."
                )


                # Part 1

                gTTS(
                    text=part1,
                    lang=detected_language,
                    slow=False
                ).save(
                    audio1_path
                )


                progress.progress(55)


                # Part 2

                if part2:

                    gTTS(
                        text=part2,
                        lang=detected_language,
                        slow=False
                    ).save(
                        audio2_path
                    )

                else:

                    # Create silent audio if part 2 doesn't exist
                    audio2_path = None


                progress.progress(65)


                # Part 3

                if part3:

                    gTTS(
                        text=part3,
                        lang=detected_language,
                        slow=False
                    ).save(
                        audio3_path
                    )

                else:

                    audio3_path = None


                progress.progress(70)


                # =================================================
                # STEP 7 - LOAD AUDIO USING LIBROSA
                # =================================================

                status_text.write(
                    "🎵 Processing audio with Librosa..."
                )


                audio1, sr1 = librosa.load(
                    audio1_path,
                    sr=None
                )


                audio_parts = [
                    audio1
                ]


                # Part 2

                if audio2_path is not None:

                    audio2, sr2 = librosa.load(
                        audio2_path,
                        sr=None
                    )

                    if sr2 != sr1:

                        audio2 = librosa.resample(
                            audio2,
                            orig_sr=sr2,
                            target_sr=sr1
                        )

                    audio_parts.append(
                        audio2
                    )


                # Part 3

                if audio3_path is not None:

                    audio3, sr3 = librosa.load(
                        audio3_path,
                        sr=None
                    )

                    if sr3 != sr1:

                        audio3 = librosa.resample(
                            audio3,
                            orig_sr=sr3,
                            target_sr=sr1
                        )

                    audio_parts.append(
                        audio3
                    )


                progress.progress(85)


                # =================================================
                # STEP 8 - COMBINE AUDIO
                # =================================================

                status_text.write(
                    "🔗 Combining audio sections..."
                )


                final_audio = np.concatenate(
                    audio_parts
                )


                # =================================================
                # STEP 9 - SAVE FINAL AUDIO
                # =================================================

                output_path = os.path.join(
                    temp_dir,
                    "PDF2Voice_Final_Audio.wav"
                )


                sf.write(
                    output_path,
                    final_audio,
                    sr1
                )


                progress.progress(100)


                # =================================================
                # STEP 10 - READ AUDIO
                # =================================================

                with open(
                    output_path,
                    "rb"
                ) as audio_file:

                    st.session_state.audio_bytes = (
                        audio_file.read()
                    )


                # =================================================
                # SUCCESS
                # =================================================

                status_text.write(
                    "✅ Audio generated successfully!"
                )

                st.success(
                    "🎉 Your audio is ready!"
                )


                # =================================================
                # INFORMATION
                # =================================================

                st.write(
                    f"🌐 Language: `{detected_language}`"
                )

                st.write(
                    f"📄 Section 1: {len(part1)} characters"
                )

                st.write(
                    f"📄 Section 2: {len(part2)} characters"
                )

                st.write(
                    f"📄 Section 3: {len(part3)} characters"
                )


                # =================================================
                # AUDIO PLAYER
                # =================================================

                st.audio(
                    st.session_state.audio_bytes,
                    format="audio/wav"
                )


                # =================================================
                # CLEANUP
                # =================================================

                if os.path.exists(pdf_path):

                    os.remove(pdf_path)

                if os.path.exists(audio1_path):

                    os.remove(audio1_path)

                if (
                    audio2_path is not None
                    and os.path.exists(audio2_path)
                ):

                    os.remove(audio2_path)

                if (
                    audio3_path is not None
                    and os.path.exists(audio3_path)
                ):

                    os.remove(audio3_path)


            except Exception as e:

                st.error(
                    f"❌ Error: {str(e)}"
                )


        generate_audio_dialog()


# ============================================================
# COLUMN 3 - DOWNLOAD
# ============================================================

with col3:

    if st.session_state.audio_bytes is not None:

        st.download_button(
            "⬇️ Download Audio",
            data=st.session_state.audio_bytes,
            file_name="PDF2Voice_Final_Audio.wav",
            mime="audio/wav",
            use_container_width=True
        )

    else:

        st.button(
            "⬇️ Download Audio",
            disabled=True,
            use_container_width=True
        )
