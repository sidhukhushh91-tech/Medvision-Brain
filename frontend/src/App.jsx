import React, { useEffect, useRef, useState } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "")
).trim().replace(/\/+$/, "");
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/jpeg", "image/png"];
const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png"];

function Icon({ name, size = 20 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  if (name === "brain") {
    return <svg {...common}><path d="M12 18V5a3 3 0 0 0-5.8-1.1A4 4 0 0 0 4 11.5a4 4 0 0 0 2 6.9A3.5 3.5 0 0 0 12 18Zm0 0V5a3 3 0 0 1 5.8-1.1A4 4 0 0 1 20 11.5a4 4 0 0 1-2 6.9A3.5 3.5 0 0 1 12 18ZM8 8h.01M16 8h.01M7 14h.01m9.99 0h.01M12 12h.01" /></svg>;
  }
  if (name === "upload") {
    return <svg {...common}><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" /></svg>;
  }
  if (name === "shield") {
    return <svg {...common}><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></svg>;
  }
  if (name === "image") {
    return <svg {...common}><rect x="3" y="3" width="18" height="18" rx="3" /><circle cx="8.5" cy="8.5" r="1.5" /><path d="m21 15-5-5L5 21" /></svg>;
  }
  if (name === "activity") {
    return <svg {...common}><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>;
  }
  if (name === "clock") {
    return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>;
  }
  if (name === "arrow") {
    return <svg {...common}><path d="M5 12h14m-6-6 6 6-6 6" /></svg>;
  }
  if (name === "close") {
    return <svg {...common}><path d="m18 6-12 12M6 6l12 12" /></svg>;
  }
  return null;
}

function formatLabel(label) {
  return label.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function App() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    let active = true;
    if (!API_URL) {
      setApiStatus("offline");
      return () => { active = false; };
    }

    fetch(`${API_URL}/api/health`)
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then((health) => active && setApiStatus(health.model_loaded ? "online" : "offline"))
      .catch(() => active && setApiStatus("offline"));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function selectFile(selected) {
    setError("");
    setResult(null);
    if (!selected) return;

    const extension = `.${selected.name.split(".").pop()}`.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(extension) || !ACCEPTED_TYPES.includes(selected.type)) {
      setFile(null);
      setError("Choose a JPG, JPEG, or PNG image.");
      return;
    }
    if (selected.size > MAX_FILE_SIZE) {
      setFile(null);
      setError("This image is larger than 10 MB. Choose a smaller file.");
      return;
    }
    setFile(selected);
  }

  async function analyzeImage() {
    if (!file || loading) return;
    setLoading(true);
    setError("");
    setResult(null);

    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch(`${API_URL}/api/predict`, { method: "POST", body: form });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "The analysis could not be completed.");
      }
      setResult(payload);
    } catch (requestError) {
      setError(requestError.message || "Could not connect to the analysis service. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="MedVision AI home">
          <span className="brand-mark"><Icon name="brain" size={23} /></span>
          <span className="brand-copy"><strong>MedVision<span>AI</span></strong><small>IMAGING INTELLIGENCE</small></span>
        </a>
        <div className="topbar-right">
          <span className="environment-label"><span className={`status-dot ${apiStatus}`} />{apiStatus === "online" ? "Analysis service online" : apiStatus === "checking" ? "Connecting to service" : "Analysis service offline"}</span>
          <span className="secure-label"><Icon name="shield" size={16} /> Local processing</span>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span /> EDUCATIONAL IMAGING TOOL</div>
            <h1>Brain MRI<br /><span>Image Classifier</span></h1>
            <p>Explore an AI model's classification of a brain MRI image. Upload a scan to view its predicted category and model scores.</p>
            <div className="hero-meta">
              <span><Icon name="activity" size={17} /> Four-class model</span>
              <i />
              <span><Icon name="shield" size={17} /> Images processed locally</span>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
            <div className="brain-disc"><Icon name="brain" size={94} /></div>
            <span className="art-cross cross-one">+</span><span className="art-cross cross-two">+</span>
            <span className="art-pulse pulse-one" /><span className="art-pulse pulse-two" />
          </div>
          <div className="hero-caption">AI-ASSISTED IMAGE CLASSIFICATION <span>•</span> FOR LEARNING</div>
        </section>

        <div className="disclaimer">
          <span className="disclaimer-icon"><Icon name="shield" size={19} /></span>
          <div><strong>For educational use only</strong><p>This tool is not a medical device and cannot diagnose, rule out, or guide treatment for any condition. Never use these results for clinical decisions.</p></div>
          <span className="disclaimer-tag">NOT FOR DIAGNOSIS</span>
        </div>

        <div className="workspace-heading">
          <div><span className="section-kicker">ANALYSIS WORKSPACE</span><h2>Start an image analysis</h2></div>
          <div className="privacy-note"><span className="privacy-lock"><Icon name="shield" size={16} /></span><span><strong>Privacy first</strong><small>Images are not retained</small></span></div>
        </div>

        <section className="workspace">
          <div className="panel upload-panel">
            <div className="panel-title"><span className="step-number">01</span><div><h3>Upload MRI image</h3><p>Select a JPG, JPEG, or PNG image to get started.</p></div></div>

            <div
              className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => { event.preventDefault(); setDragging(false); selectFile(event.dataTransfer.files[0]); }}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }}
              role="button"
              tabIndex={0}
              aria-label="Choose or drop an MRI image"
            >
              <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,image/jpeg,image/png" hidden onChange={(event) => selectFile(event.target.files[0])} />
              <div className="upload-icon"><Icon name="upload" size={24} /></div>
              <strong>{file ? "Image ready for analysis" : "Drop your image here"}</strong>
              <span className="dropzone-sub">{file ? "Your image is ready to be analyzed" : "or click to browse from your device"}</span>
              <span className="file-types"><span>JPG</span><span>JPEG</span><span>PNG</span><i /> Up to 10 MB</span>
            </div>

            {error && <div className="error-message" role="alert"><span>!</span>{error}</div>}

            {file && (
              <div className="selected-file">
                <div className="file-thumb"><img src={previewUrl} alt="Selected MRI preview" /></div>
                <div className="file-info"><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toFixed(2)} MB · Image ready</span></div>
                <button className="icon-button" type="button" onClick={(event) => { event.stopPropagation(); reset(); }} aria-label="Remove selected image"><Icon name="close" size={18} /></button>
              </div>
            )}

            <button className="analyze-button" type="button" disabled={!file || loading || apiStatus === "offline"} onClick={analyzeImage}>
              {loading ? <><span className="spinner" /> Analyzing image…</> : <>Analyze image <Icon name="arrow" size={18} /></>}
            </button>
            {apiStatus === "offline" && <p className="service-hint">{API_URL ? "Analysis service is unavailable. Check that the backend is running." : "Analysis API is not configured. Set VITE_API_URL to your deployed backend URL."}</p>}
            <div className="upload-footnote"><Icon name="shield" size={15} /> Images are not retained after the request.</div>
          </div>

          <div className={`panel result-panel ${result ? "has-result" : ""}`}>
            <div className="panel-title"><span className="step-number">02</span><div><h3>Classification result</h3><p>{result ? "Model output for your uploaded image." : "Your results will appear here after analysis."}</p></div></div>
            {!result ? (
              <div className="empty-result">
                <div className="empty-visual"><span className="scan-line" /><Icon name="image" size={40} /></div>
                <strong>Ready when you are</strong>
                <p>Upload a brain MRI image and run the classifier to see the model output.</p>
                <div className="empty-steps"><span><b>1</b> Upload image</span><i /><span><b>2</b> View results</span></div>
              </div>
            ) : (
              <div className="result-content" aria-live="polite">
                <div className="result-preview"><img src={previewUrl} alt="Analyzed brain MRI" /><span><Icon name="image" size={14} /> {file?.name}</span></div>
                <div className="prediction-card">
                  <div className="prediction-label"><span className="result-check">✓</span><span>TOP PREDICTION</span></div>
                  <h4>{formatLabel(result.predicted_class)}</h4>
                  <div className="confidence-row"><span>Model score</span><strong>{result.confidence.toFixed(1)}<small>%</small></strong></div>
                  <div className="confidence-track"><span style={{ width: `${Math.min(result.confidence, 100)}%` }} /></div>
                  <p className="score-note">Model score, not a clinically calibrated probability.</p>
                </div>
                <div className="scores-heading"><strong>Class scores</strong><span>{result.scores.length} classes</span></div>
                <div className="score-list">
                  {result.scores.map((score) => (
                    <div className="score-item" key={score.label}>
                      <div className="score-name"><span>{formatLabel(score.label)}</span><strong>{score.score.toFixed(1)}%</strong></div>
                      <div className="score-track"><span style={{ width: `${Math.min(score.score, 100)}%` }} /></div>
                    </div>
                  ))}
                </div>
                <div className="result-footer"><span><Icon name="clock" size={15} /> {result.inference_seconds.toFixed(2)}s processing</span><button type="button" onClick={reset}>Analyze another <Icon name="arrow" size={15} /></button></div>
                <p className="result-disclaimer">{result.disclaimer}</p>
              </div>
            )}
          </div>
        </section>

        <section className="info-strip">
          <div className="info-icon"><Icon name="activity" size={20} /></div>
          <div><strong>About this model</strong><p>This four-class model was trained on a public brain MRI dataset. Performance on that dataset does not establish real-world clinical reliability.</p></div>
          <a href="https://huggingface.co/Devarshi/Brain_Tumor_Classification" target="_blank" rel="noreferrer">Model details <Icon name="arrow" size={15} /></a>
        </section>
      </main>

      <footer><a className="footer-brand" href="#"><span className="footer-mark"><Icon name="brain" size={17} /></span> MedVision<span>AI</span></a><span>Educational prototype · Always seek professional medical advice for health concerns.</span><span className="footer-status"><i /> No image retention</span></footer>
    </div>
  );
}
