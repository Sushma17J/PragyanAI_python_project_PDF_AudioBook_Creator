import streamlit as st
import PyPDF2
import librosa
import soundfile as sf
import numpy as np
import tempfile
import os

from gtts import gTTS


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF2Voice",
    page_icon="🔊",
    layout="centered"
)


# ============================================================
# TITLE
# ============================================================

st.title("🔊 PDF2Voice")

st.markdown(
    "### Convert PDF text into a single audio file"
)

st.write(
    "Upload a PDF, generate audio from the first "
    "3000 characters, and download the final audio."
)


# ============================================================
# SESSION STATE
# ============================================================

if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None

if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None


# ============================================================
# UPLOAD PDF
# ============================================================

uploaded_file = st.file_uploader(
    "Select your PDF",
    type=["pdf"],
    label_visibility="collapsed"
)


if uploaded_file is not None:

    st.session_state.pdf_file = uploaded_file

    st.success(
        f"✅ PDF uploaded: {uploaded_file.name}"
    )


# ============================================================
# BUTTONS
# ============================================================

col1, col2, col3 = st.columns(3)


# ============================================================
# GENERATE AUDIO
# ============================================================

with col2:

    generate_clicked = st.button(
        "🎙️ Generate Audio",
        use_container_width=True
    )


# ============================================================
# GENERATE AUDIO PROCESS
# ============================================================

if generate_clicked:

    if st.session_state.pdf_file is None:

        st.warning(
            "⚠️ Please upload a PDF first."
        )

    else:

        # ----------------------------------------------------
        # Popup Dialog
        # ----------------------------------------------------

        @st.dialog("🎙️ Generate Audio")
        def generate_audio_dialog():

            st.write(
                "Your PDF is being processed..."
            )

            progress = st.progress(0)

            status_text = st.empty()

            try:

                # =================================================
                # STEP 1 - READ PDF
                # =================================================

                status_text.write(
                    "📄 Extracting text from PDF..."
                )

                progress.progress(20)

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


                # =================================================
                # STEP 2 - EXTRACT TEXT
                # =================================================

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
                        "❌ No readable text found."
                    )

                    os.remove(pdf_path)

                    return


                progress.progress(40)

                # =================================================
                # STEP 3 - FIRST 3000 CHARACTERS
                # =================================================

                part1 = full_text[0:1000]

                part2 = full_text[1000:2000]

                part3 = full_text[2000:3000]


                status_text.write(
                    "✂️ Dividing text into three sections..."
                )


                # =================================================
                # STEP 4 - TEXT TO SPEECH
                # =================================================

                progress.progress(50)

                status_text.write(
                    "🔊 Converting text to speech..."
                )

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


                gTTS(
                    text=part1,
                    lang="en",
                    slow=False
                ).save(audio1_path)


                progress.progress(60)


                gTTS(
                    text=part2,
                    lang="en",
                    slow=False
                ).save(audio2_path)


                progress.progress(70)


                gTTS(
                    text=part3,
                    lang="en",
                    slow=False
                ).save(audio3_path)


                # =================================================
                # STEP 5 - LOAD AUDIO USING LIBROSA
                # =================================================

                status_text.write(
                    "🎵 Processing audio with Librosa..."
                )

                audio1, sr1 = librosa.load(
                    audio1_path,
                    sr=None
                )

                audio2, sr2 = librosa.load(
                    audio2_path,
                    sr=None
                )

                audio3, sr3 = librosa.load(
                    audio3_path,
                    sr=None
                )


                # =================================================
                # STEP 6 - SAME SAMPLE RATE
                # =================================================

                if sr2 != sr1:

                    audio2 = librosa.resample(
                        audio2,
                        orig_sr=sr2,
                        target_sr=sr1
                    )


                if sr3 != sr1:

                    audio3 = librosa.resample(
                        audio3,
                        orig_sr=sr3,
                        target_sr=sr1
                    )


                progress.progress(85)


                # =================================================
                # STEP 7 - MERGE AUDIO
                # =================================================

                status_text.write(
                    "🔗 Combining all three audio sections..."
                )

                final_audio = np.concatenate(
                    [
                        audio1,
                        audio2,
                        audio3
                    ]
                )


                # =================================================
                # STEP 8 - SAVE FINAL AUDIO
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

                status_text.write(
                    "✅ Audio generated successfully!"
                )


                # =================================================
                # STORE AUDIO
                # =================================================

                with open(
                    output_path,
                    "rb"
                ) as audio_file:

                    st.session_state.audio_bytes = (
                        audio_file.read()
                    )


                st.session_state.audio_path = (
                    output_path
                )


                # =================================================
                # RESULT
                # =================================================

                st.success(
                    "🎉 Your audio is ready!"
                )

                st.info(
                    "The audio contains three consecutive "
                    "1000-character sections."
                )

                st.audio(
                    st.session_state.audio_bytes,
                    format="audio/wav"
                )

                st.session_state.audio_generated = True


                # Cleanup PDF
                os.remove(pdf_path)


            except Exception as e:

                st.error(
                    f"❌ Error: {str(e)}"
                )


        generate_audio_dialog()


# ============================================================
# DOWNLOAD AUDIO
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
