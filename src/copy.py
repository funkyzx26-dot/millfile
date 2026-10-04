# -*- coding: utf-8 -*-
"""All English site copy for MillFile. Consumed by build.py — edit text here,
not in templates. Straight quotes only (FAQ strings are checked verbatim
against visible page text by the build)."""

BRAND = "MillFile"

# Target-size landing pages: key = target in KB, slug = compress-pdf-to-<slug>
SIZES = {
    100: {
        "slug": "100kb",
        "meta_desc": "Compress PDF to 100 KB online, free and unlimited. Scans and ID copies fit 100 KB upload caps. Runs in your browser - file never uploaded.",
        "h1": "Compress PDF to 100 KB",
        "lead": "Passport scans, ID copies and certificates are routinely capped at 100 KB by application portals. Drop your PDF below and compress it to fit under 100 KB - free, unlimited, no sign-up, no watermark. The file is processed on this device and never uploaded.",
        "why_title": "Why upload forms demand 100 KB",
        "why": [
            "A 100 KB ceiling shows up wherever identity documents are submitted: visa applications, government recruitment portals, university admission systems and scholarship forms. Exceed it by a few kilobytes and the upload button refuses the file, usually with a one-line error and no hint about what to do.",
            "Scanned pages saved from a scanner or a phone app are typically 300 KB to 2 MB each, so the form loses before you start. MillFile rebuilds the document to fit under 100 KB: it first tries a lossless repack that keeps text sharp, then reduces page detail in small steps only as far as needed. Everything happens in your browser, so scans of your passport stay on your machine."
        ],
        "faq": [
            ("How do I compress a PDF to 100 KB?",
             "Keep the 100 KB target selected above, drop the file, and download it when the badge turns green. The page works down until the result fits under 100 KB, ready for the form that asked for it."),
            ("Will my scanned ID still be readable?",
             "Yes, to the limit you chose. MillFile stops reducing as soon as the file fits - it never over-compresses past what you asked for, so the text stays as clear as 100 KB allows."),
            ("Is my document uploaded to a server?",
             "No. The whole process runs inside this browser tab on your device. Your file is read from disk and written back for download without any network request."),
            ("Is there a cost or daily limit?",
             "None. MillFile is free with no account, no watermark and no quota. Compress one document or fifty in the same session."),
            ("Can I compress a PDF to 50 KB or lower than 100 KB?",
             "No - 100 KB is the smallest target selectable on this site. Set it anyway and read the badge: a document that cannot go smaller shows the minimum size actually reached, which is the floor of that file. For a 50 KB form the scan itself has to be lighter - lower resolution, grayscale, one page at a time."),
            ("How do I compress a PDF to 100 KB on an iPhone?",
             "Open this page in Safari or Chrome on the iPhone and tap the drop box. The picker shows the Files app, where camera scans and mail attachments are kept, and the finished PDF is saved back to Files. The passport copy never leaves the phone, because there is no upload step to begin with."),
            ("Will a 100 KB scan pass a passport or visa upload rule?",
             "It depends on which number the rule enforces. A rule that only caps file size is met exactly. A rule that also demands a minimum resolution may not be, because a re-rendered page lands between roughly 45 and 144 dots per inch - readable, but modest. When both numbers appear, choose the largest cap the rule allows."),
            ("Is the 100 KB limit per file or per application?",
             "Check the wording, because MillFile answers per file: every document you drop is rebuilt to fit under 100 KB on its own. A portal that wants 100 KB for the whole application is a different job - combine the pages into one PDF first, then compress that.")
        ]
    },
    200: {
        "slug": "200kb",
        "meta_desc": "Compress PDF to 200 KB in your browser, free. Signed forms, transcripts and certificates fit 200 KB upload caps. No upload, no sign-up.",
        "h1": "Compress PDF to 200 KB",
        "lead": "Signed forms, transcripts and certificates often hit a 200 KB upload cap. Compress your PDF to fit under 200 KB right here in the browser - free, unlimited, and the file never leaves this device.",
        "why_title": "Where the 200 KB limit comes from",
        "why": [
            "Two hundred kilobytes is a favourite ceiling for education and HR systems: scholarship portals, exam boards, job applications and corporate upload forms all state PDF up to 200 KB. A document exported from Word or fed through a document scanner lands well above that number on the first try.",
            "Drop the file below and MillFile rebuilds it to fit under 200 KB. A lossless repack runs first, which keeps selectable text razor sharp. Only if the file is still too heavy does the page reduce rendered detail, one small step at a time, checking after each step. Because the work happens on your device, confidential records stay confidential."
        ],
        "faq": [
            ("How do I make my PDF 200 KB or smaller?",
             "Choose the 200 KB target, drop the file, and download the result when processing finishes. The badge on each row shows the final size and exactly how much was saved."),
            ("Does compressing damage the document?",
             "Only when it must. The lossless rebuild comes first and changes no visible quality. Page detail is reduced only as far as needed to get under 200 KB, never further."),
            ("Can I compress several files at once?",
             "Yes - drop a whole batch. Files are processed in order, and once more than one succeeds you can download them together as a zip."),
            ("Do I need to install anything?",
             "No. MillFile runs in the browser on Windows, Mac, Linux and phones. Nothing to install, nothing to register."),
            ("Can I make a PDF 200 KB without losing searchable text?",
             "Yes whenever the lossless rebuild gets there first. That pass changes no pixels, so text stays selectable and searchable, and documents exported from Word often land under 200 KB with it alone. Pages that must be re-rendered become images and lose searchability. If the portal requires searchable text, test the compressed copy before uploading."),
            ("How do I compress a PDF to 200 KB in Chrome?",
             "Open this page in Chrome, click the drop box and pick the file. Chrome on Windows, Mac, Linux, Chromebook and Android all run the same on-device pipeline, with no extension and no sign-in, and the result arrives as an ordinary Chrome download."),
            ("Is it safe to compress a resume or transcript here?",
             "Those are the files people least want copied somewhere, and here there is nowhere to copy them to. The document is read from disk, rebuilt in memory and handed back for download, with no account to attach it to and no server holding a second copy."),
            ("Does compressing to 200 KB affect fonts?",
             "The lossless pass keeps every font and character exactly as exported. A re-rendered page gives up the font file and keeps its appearance as an image, so the type still looks right on screen and in print, and the page count and dimensions do not change.")
        ]
    },
    300: {
        "slug": "300kb",
        "meta_desc": "Compress PDF to 300 KB online for free. Passes 300 KB upload caps on application portals. Unlimited, no sign-up, files never uploaded.",
        "h1": "Compress PDF to 300 KB",
        "lead": "Application portals ask for PDF up to 300 KB all over the web - recruitment, admissions, visas, tenders. This page compresses your PDF to fit under 300 KB in seconds. Free, unlimited, no sign-up, no watermark, and the file never leaves your device.",
        "why_title": "Why so many forms cap at 300 KB",
        "why": [
            "Three hundred kilobytes is one of the most common document limits online. Government recruitment forms, university applications, tender submissions and professional registration systems set it to keep their storage light, and they reject anything heavier with a single line of error text - no guidance, no second chance.",
            "Print-ready PDFs embed full-resolution images and whole fonts, so they reach one or two megabytes before you notice. MillFile gets yours under the line without sending it anywhere: a lossless rebuild handles text documents in seconds, and scanned pages are re-rendered in small steps until they fit. What you download keeps the highest quality that still fits under 300 KB."
        ],
        "faq": [
            ("How do I compress a PDF to 300 KB?",
             "The 300 KB target is pre-selected on this page - drop your file and download it once the badge turns green. A typical document takes a few seconds from drop to download."),
            ("Why is my PDF too big for the upload form?",
             "Portals cap file size at a fixed number, while scanners and Word export far above it. The form is not broken and your document is not wrong - it simply has not been compressed to the stated cap yet."),
            ("Is it safe for confidential documents?",
             "Yes. Compression happens in your browser and the file is never uploaded. You can disconnect from the internet after the page loads and it still works."),
            ("What if the file cannot reach 300 KB?",
             "Very dense scans have a floor. When a document cannot fit, the badge shows the smallest size achieved so you know what you can upload, or what to re-scan at a lower resolution."),
            ("How small can a scanned PDF actually get?",
             "By the page, not by the target. A text page repacks to a few kilobytes, while a busy photo page keeps a floor - the smallest image your browser can make of it. When several heavy pages add up above 300 KB, the badge reports that minimum instead of pretending the target was met."),
            ("Can I compress a PDF to 300 KB on my phone?",
             "Yes. Mobile Safari and Chrome run this page exactly as a desktop browser does: tap the box, choose the file from Files or Downloads, wait for the badge. The difference is time, since every page is rendered on the handset itself."),
            ("Are hyperlinks kept when a PDF is compressed to 300 KB?",
             "A lossless rebuild leaves page content as it is, links included. Once a page is re-rendered it is a picture, and the links, form fields and signatures on it go with it; the bookmark outline and stored document title are not carried into the new file either. If a submission needs a working link, open the compressed copy and click it."),
            ("Will a 300 KB scan meet a minimum resolution rule?",
             "Some forms state a size cap and a resolution floor at once, and the two can conflict. Re-rendered pages land between roughly 45 and 144 dots per inch, so read which number the portal really enforces and pick the largest target that satisfies it. Page dimensions stay exactly as they were.")
        ]
    },
    500: {
        "slug": "500kb",
        "meta_desc": "Compress PDF to 500 KB free in your browser. Fit 500 KB attachment and portal limits fast. No upload, no account, no watermark.",
        "h1": "Compress PDF to 500 KB",
        "lead": "Email attachments and portals often stop at 500 KB. Compress your PDF to fit under 500 KB here - free, unlimited, processed on your own device so nothing is ever uploaded.",
        "why_title": "The 500 KB ceiling in practice",
        "why": [
            "Five hundred kilobytes sits just under most email attachment allowances and appears on countless HR, insurance and municipal upload forms. It is also the first limit that scanned paperwork and image-rich exports break, because a single photo on a page can weigh more than the whole budget.",
            "MillFile reworks the file until it fits under 500 KB. The lossless rebuild handles documents that are merely uncompressed, and pages that still overshoot are re-rendered with a little less detail - heavy pages absorb the reduction while clean pages keep theirs. Drop the file below to try it; at no point does the document leave this device."
        ],
        "faq": [
            ("How do I compress a PDF to 500 KB?",
             "Keep the 500 KB target selected, drop the file above, and download the result when the badge shows the new size. The whole pass runs locally in a couple of seconds for typical documents."),
            ("Will images in my PDF get blurry?",
             "MillFile spends detail only where it must. Pages with little content keep their quality, and photo-heavy pages are reduced just enough to keep the whole file under 500 KB."),
            ("Can I use this on my phone?",
             "Yes. MillFile works in mobile browsers the same way - choose the target, pick a file from your device, and download the compressed copy."),
            ("Do you store or read my files?",
             "No. There is no upload step and no backend. The file is read and rewritten in browser memory, and the download comes straight from that memory."),
            ("Can I reduce a PDF to 500 KB without losing searchable text?",
             "Often, yes. A 500 KB target is roomy, and a document that clears it on the lossless pass keeps text fully selectable and searchable. Only pages that still overshoot become images, and those pages lose searchability while staying perfectly readable."),
            ("Which PDFs can this page compress?",
             "Anything that breaks the 500 KB line: photo scans, illustrated reports, exports with embedded images, scans saved at full resolution. Password-protected files are the exception - the badge marks them password-protected, and they have to be unlocked before anything can be done."),
            ("How do I compress a PDF to 500 KB in Chrome?",
             "Open this page in Chrome, click the drop box and choose the file. The pipeline is the same on Windows, Mac, Linux, Chromebook and Android Chrome: nothing is installed, nothing is uploaded, and the compressed PDF arrives in your downloads folder.")
        ]
    },
    1024: {
        "slug": "1mb",
        "meta_desc": "Compress PDF to 1 MB free online. Fit 1 MB upload limits while keeping photos as sharp as possible. Processed in your browser, never uploaded.",
        "h1": "Compress PDF to 1 MB",
        "lead": "Keep a photo-rich PDF under a 1 MB upload limit. Compress to 1 MB in your browser - free, unlimited, no account, and your file is never uploaded to anywhere.",
        "why_title": "When one megabyte is the line",
        "why": [
            "One megabyte is the standard allowance on many scholarship, insurance and legal filing portals, and it is the first limit that photo-heavy documents cross. Pages with scans, screenshots or exported diagrams push the total over the cap even when the text itself weighs almost nothing.",
            "MillFile compresses with a budget: the whole file has to fit under 1 MB, so heavy pages give up detail first and text-only pages keep theirs. A lossless rebuild runs before anything is re-rendered, so many documents reach the target with no quality change at all. Processing stays on your device from drop to download."
        ],
        "faq": [
            ("How do I compress a PDF to 1 MB?",
             "Select the 1 MB target, drop the file, and download the result when processing completes. The badge reports the final size and the percentage saved."),
            ("Does the compression keep my text selectable?",
             "When a lossless rebuild is enough, yes - text stays fully selectable. If pages must be re-rendered to meet the limit, those pages become images, which is the usual trade for meeting a hard cap."),
            ("How many files can I process?",
             "As many as you like in one session. Drop them together, let the queue run, then take the whole batch as a zip."),
            ("Is MillFile really free?",
             "Yes - no account, no watermark, no daily quota, no premium tier hiding the good options."),
            ("Does compressing to 1 MB reduce DPI?",
             "The lossless pass does not touch resolution at all. Pages that are re-rendered come out between roughly 45 and 144 dots per inch, and very large sheets below that, because the browser limits how much it will draw at once. That is comfortable for reading and printing at normal sizes; a rule demanding 300 DPI will not accept it."),
            ("Are links, bookmarks and form fields preserved at 1 MB?",
             "Pages that keep their real text keep their clickable links. A page that has to be re-rendered becomes an image and loses its links, form fields and signature appearance, and the rebuilt file carries no bookmark outline or stored title in either case. Check those before filing with a court or permit desk."),
            ("Can I compress a PDF to 1 MB on an iPhone?",
             "Yes - open this page in Safari or Chrome, tap the box and pick the file from Files. A photo-heavy document takes longer on a handset than on a laptop, since pages are rendered one at a time on the device, so a very long one is more comfortable on a computer.")
        ]
    },
    2048: {
        "slug": "2mb",
        "meta_desc": "Compress PDF to 2 MB free. Keep diagrams and photos legible under 2 MB caps on court, permit and council forms. Browser-based, no upload.",
        "h1": "Compress PDF to 2 MB",
        "lead": "Drop a large PDF and keep it under a 2 MB cap. Free browser-based compression with no upload, no account and no watermark - built for diagrams, photos and multi-page documents.",
        "why_title": "Fitting diagrams under two megabytes",
        "why": [
            "Two megabyte caps are common on court, permit and council submission systems that still want legible diagrams, plans and photographs. Documents in that class are heavy by nature: every embedded image adds its own weight, and the total drifts past the limit during ordinary editing.",
            "MillFile spends the budget where it matters. Each page competes for space in the 2 MB total, so dense, image-heavy pages are reduced while light pages keep their full detail - and a lossless rebuild runs first, which is enough for plenty of documents. The whole pipeline runs on your device, so plans and filings never touch a server."
        ],
        "faq": [
            ("How do I compress a PDF to 2 MB?",
             "Choose the 2 MB target above, drop the file, and download it when the badge confirms the new size. Large documents page through quickly and report progress while they work."),
            ("Can it handle multi-page documents?",
             "Yes. Pages are processed one at a time with a shared size budget, so a long report compresses as a whole instead of each page being cut to the same level blindly."),
            ("What happens to pages that are already small?",
             "They keep their quality. Reduction is applied only where a page would otherwise break the 2 MB total."),
            ("Where do my files go?",
             "Nowhere. MillFile has no backend - reading, compressing and downloading all happen inside this browser tab."),
            ("Can I compress to 2 MB without losing searchable text?",
             "Frequently, yes. A 2 MB allowance is wide enough that many documents finish after the lossless rebuild, which leaves text fully selectable and searchable. Only the pages that still overshoot become images, and they stay readable even though they stop being searchable."),
            ("Will my diagrams still be legible at 2 MB?",
             "That is the point of this target, so the budget is spent to keep them readable: heavy pages give up detail first and light pages keep theirs. Re-rendered pages land between roughly 45 and 144 dots per inch, and a large drawing sheet less. Open the result at full zoom before sending a plan to a council."),
            ("Do links and form fields survive compression to 2 MB?",
             "Real text pages keep their links. Pages that are re-rendered turn into pictures and lose links, fillable fields and signatures with them, and no version of the output keeps the bookmark outline or the stored document title. If the filing needs either, send the original document.")
        ]
    },
}

INDEX = {
    "meta_desc": "Compress a PDF to an exact size - 100 KB, 300 KB, 1 MB and more. Free, unlimited, no sign-up. Processed in your browser, never uploaded.",
    "h1": "Compress PDF to an Exact Size",
    "sub": "Free, unlimited, no sign-up - <b>your files never leave this device</b>",
    "intro": "Upload forms everywhere enforce fixed PDF limits: 100 KB for ID scans, 300 KB for applications, 1 MB for attachments. MillFile rebuilds your document to fit the exact limit you choose. Everything runs in this browser tab - no account, no watermark, and no server ever sees your file.",
    "steps": [
        ("Choose your target", "Pick the size the form demands, from 100 KB to 2 MB. Every common target has its own page with a direct link you can bookmark or share."),
        ("Drop your PDF", "Files are read straight from your device. A lossless rebuild runs first; if the result is still too big, pages are reduced in small steps until they fit the target."),
        ("Download and upload", "The badge shows the final size and how much was saved. Download one file or take the whole batch as a zip, then upload with confidence.")
    ],
    "faq": [
        ("What is MillFile?",
         "A browser tool that compresses a PDF to a precise size limit - 100 KB, 300 KB, 1 MB or anything between. It is free, needs no account, and never uploads your files."),
        ("Why do websites reject my PDF?",
         "They cap file size, commonly somewhere between 100 KB and 1 MB, while scanners and Word export well above those numbers. Compressing to the stated cap is the whole fix."),
        ("Is there a file size or usage limit?",
         "There is no account, no watermark and no daily quota. Larger files simply take longer, because pages are rendered one at a time on your own device."),
        ("How is this different from online converters?",
         "Most converters upload your document to a server, then queue you or charge for higher limits. MillFile works entirely on your device, which keeps confidential documents confidential and keeps the price at zero."),
        ("Can I compress a PDF to 50 KB or 10 KB?",
         "The smallest target you can pick here is 100 KB, so a 50 KB form cannot be answered directly. Every document also has a floor: when a file will not fit, the badge reports the smallest size actually reached instead of guessing. To get under 100 KB the source has to shrink first - scan at a lower resolution, drop blank pages, keep one page per file."),
        ("How do I compress a PDF on an iPhone or in Chrome?",
         "Open the tool in Chrome on Windows, Mac, Linux or Android and click the box to choose a file. On an iPhone or iPad the same tap opens the Files app, where camera scans and mail attachments live, and the finished PDF is saved back there. Neither path uploads anything. A long document takes longer on a phone, because pages are rendered one at a time."),
        ("Are links, bookmarks and form fields preserved?",
         "When the lossless rebuild is enough, pages keep their text, fonts and clickable links. Pages that must be re-rendered become pictures, and the links, fillable fields and signatures on them are gone. Either way the bookmark outline and the stored document title do not carry into the new file. If a submission needs a live form, send the original.")
    ]
}

HOW = {
    "meta_desc": "How MillFile compresses PDFs: a lossless rebuild first, then adaptive page rendering with a shared size budget. All inside your browser.",
    "h1": "How MillFile compresses PDFs",
    "lede": "There is no server behind this site. Everything below happens inside this browser tab, which is why your file can stay on your device and still get smaller.",
    "sections": [
        ("Step 1 - a lossless rebuild",
         ["The moment a file is dropped, MillFile rebuilds its internal structure: duplicate objects collapse, unused data is dropped, and objects are packed more tightly. No pixels change and no text changes - for many documents, especially ones exported straight from Word or a PDF printer, this alone brings the file under the target."]),
        ("Step 2 - adaptive page rendering",
         ["If the rebuilt file is still too big, each page is rendered to an image and re-encoded at a chosen quality. The trick is the budget: the target size is divided across the remaining pages, and every page takes the highest quality that still fits its share.",
          "Light pages finish early and keep high quality; heavy pages step down through smaller quality levels until they fit. If a page cannot fit even at the lowest setting, it takes the smallest it can and the badge reports the honest final size instead of pretending."]),
        ("Step 3 - a fresh PDF",
         ["The chosen page images are packed into a new PDF with the same page dimensions, so the document still prints and displays at the right proportions. The result is downloaded from memory straight to your device."]),
        ("What this changes, honestly",
         ["When the lossless rebuild is enough, your PDF keeps selectable text and identical appearance. When pages have to be re-rendered, those pages become images: text is still perfectly readable, but it is no longer selectable or searchable. That is the standard trade for meeting a hard upload cap, and the lossless path always runs first to avoid it whenever possible.",
          "Practical tip: if a file must reach a very small cap, scan or export at a moderate resolution to begin with, remove blank or duplicate pages beforehand, and let MillFile handle the rest."])
    ]
}

PRIVACY = {
    "meta_desc": "MillFile privacy: your PDF is processed in your browser and never uploaded. No accounts, no tracking, no server-side storage.",
    "h1": "Privacy: nothing leaves your device",
    "lede": "MillFile is a static page with no backend. The strongest privacy claim is the simplest one to verify yourself.",
    "sections": [
        ("Your file never uploads",
         ["When you drop a PDF, the page reads it with the browser's local file API and keeps it in memory. Compression uses only that memory copy, and the download is generated from the same copy. No request carries your document anywhere - open the developer tools network tab and you will see the file appear in no request at all."]),
        ("No accounts, no profiles",
         ["There is no sign-up, no login and no user database. The tool cannot associate a file with a person because it never meets either."]),
        ("No tracking at this stage",
         ["The site sets no analytics cookies and loads no third-party trackers. All JavaScript - the PDF engine, the packer for zip downloads - is served from this same domain, so nothing phones home."]),
        ("What remains on your side",
         ["Files you download land in your normal downloads folder under your browser's rules. Clearing the tab clears everything the page was holding; there is nothing else to delete on our side, because there is no our side."])
    ]
}

ABOUT = {
    "meta_desc": "About MillFile: who runs it, why a browser-based PDF compressor exists, and how to get in touch.",
    "h1": "About MillFile",
    "lede": "MillFile is a small independent project with one job: get a PDF under the exact size limit a form demands, without the document ever leaving your device.",
    "sections": [
        ("Who runs this",
         ["MillFile is built and maintained by one independent developer. There is no company behind it and no team, which is also why there is no sign-up, no pricing table and no account to create.",
          "There is no upload step on this site, so no server of ours ever holds a copy of a file you process."]),
        ("What it does",
         ["Upload forms all over the web enforce a fixed PDF limit: 100 KB for an ID scan, 300 KB for an application, 1 MB for an attachment. When you miss the limit the form returns one line of error text and no hint about what to do next.",
          "MillFile rebuilds your document to fit the number you pick. A lossless rebuild runs first and keeps the text selectable; only if the file is still too large are pages re-rendered with less detail, one step at a time, until they fit. You get the finished file back as an ordinary download."]),
        ("Why it works this way",
         ["Most PDF tools ask you to upload the document to their server first. That is fine for a takeaway menu and a bad idea for a passport scan, a payslip, a medical certificate or a signed contract - which are exactly the documents people need to compress.",
          "Doing the work in the browser removes that step, and with it the queue, the daily cap and the watermark, because there is no server to pay for. The trade is time: a very large document takes longer here, since every page is rendered on your own machine.",
          "When a document cannot reach the target you chose, the badge reports the smallest size actually achieved instead of claiming success. Knowing the real floor is more useful than a reassuring number."]),
        ("Contact",
         ["Questions, bug reports and complaints all go to the same address: hello@millfile.com.",
          "If a PDF does not compress the way you expected, mention the target you chose, roughly how large the original was and whether it was a scan or an exported document. That is usually enough to reproduce it."])
    ]
}

TERMS = {
    "meta_desc": "MillFile terms of use: what the tool promises, what it does not, and where our liability ends.",
    "h1": "Terms of Use",
    "lede": "Short, plain-language terms for using MillFile. If you do not accept them, please do not use the site.",
    "sections": [
        ("Using the tool",
         ["MillFile is a free browser tool that rebuilds a PDF so it fits a size you choose. You may use it for personal or commercial documents, as often as you like, with no account and no payment.",
          "You are responsible for the documents you process and for having the right to process them. Do not use the site for anything unlawful, for material you have no permission to handle, or in any way intended to overload or interfere with it."]),
        ("What we do not promise",
         ["The tool is provided as is. Compression is a trade: to reach a small target, pages are re-rendered as images, and that can remove selectable text, hyperlinks, form fields and signatures. The site reports honestly whether the target was reached, but you must check the result yourself before submitting it anywhere that matters.",
          "We do not guarantee that a compressed file will be accepted by any particular portal, that the site will always be reachable, or that it will be free of defects. Nothing on this site is legal, immigration, tax or professional advice."]),
        ("Your files stay yours",
         ["You keep every right to your documents. Because the work happens in your browser and no file is uploaded, we never receive a copy, never store one, and have nothing to license or reuse."]),
        ("Content on this site",
         ["The text, layout and code of MillFile belong to the site. You are welcome to link to any page. Please do not copy the site wholesale or present it as your own work."]),
        ("Limits of liability",
         ["To the extent the law allows, MillFile is not liable for indirect or consequential losses arising from use of the site, including a rejected upload, a missed deadline or damage to a file. Where liability cannot be excluded, it is limited to the amount you paid to use the site, which is nothing."]),
        ("Changes to these terms",
         ["These terms may change as the site changes. The version on this page is always the current one, and continuing to use the site after a change means you accept it."]),
        ("How to reach us",
         ["Anything about these terms, including a request to correct or remove content, can be sent to hello@millfile.com."])
    ]
}

# RAW to JPG pages. Same shape as SIZES: slug is the whole path segment.
# The engine is LibRaw compiled to WebAssembly, decoded in a worker; every claim
# below was measured on a real 30 MB ARW (26 MP) before it was written.
RAW_ORDER = ["raw-to-jpg", "nef-to-jpg", "arw-to-jpg", "dng-to-jpg"]

RAW = {
    "raw-to-jpg": {
        "short": "RAW to JPG",
        "title": "Convert RAW to JPG in Your Browser - Free, No Upload",
        "meta_desc": "Convert CR2, NEF, ARW, CR3, ORF and other RAW files to full-resolution JPG in your browser. Free, no sign-up, no watermark - the file is never uploaded.",
        "h1": "Convert RAW to JPG",
        "lead": "Drop a RAW file from any major camera and get a full-resolution JPG back. The frame is decoded in your browser by LibRaw compiled to WebAssembly, so the file is never uploaded - no account, no watermark, no daily limit.",
        "why_title": "Why convert RAW in the browser",
        "why": [
            "A RAW file holds the sensor data as the camera recorded it: 12 to 14 bits per channel, no JPEG compression, and a white balance that is still a suggestion rather than a decision. That is what makes it worth editing, and it is also why the delivery step is awkward. Print shops, job portals, forums and email all want a JPG, and the usual converters ask you to upload a 30 MB file to a server before they will help.",
            "MillFile decodes the frame here, in this tab. A 26 megapixel frame takes about two to three seconds on a laptop - that is our own measurement on a 30 MB Sony file, not an estimate - and the result keeps the full sensor resolution. Larger sensors take longer, because every pixel is processed on your own machine rather than on hardware somebody else pays for."
        ],
        "faq": [
            ("Which RAW formats can I convert?",
             "Canon CR2 and CR3, Nikon NEF and NRW, Sony ARW, SRF and SR2, Adobe DNG, Fujifilm RAF, Olympus ORF, Panasonic RW2, Pentax PEF, Samsung SRW, and the other formats LibRaw recognises - the decoder behind this page covers well over a thousand camera models. A file that cannot be decoded says so on its own row instead of failing silently."),
            ("Will the JPG include my edits from Lightroom or Capture One?",
             "No. Those adjustments live in the editor's catalogue or in an XMP sidecar file, not inside the RAW, and this page only reads the RAW you hand it. What you get is the camera's own white balance and a standard demosaic: a clean full-resolution render, not a copy of an edited export. Use it when you want the picture rather than the grade."),
            ("Do I get the camera's embedded preview instead of a real decode?",
             "No - this page always decodes the full frame, which is why it takes a couple of seconds rather than a fraction of one. The trade is that the JPG is built from the sensor data at full resolution instead of from the smaller preview most cameras store alongside it."),
            ("Can I convert several files at once?",
             "Drop them together and they are converted one after another, each with its own download button. They run in sequence rather than in parallel, because a single 26 megapixel frame already needs a few hundred megabytes of working memory."),
            ("Is there a file size limit?",
             "No hard limit, but a very large file needs a capable device. The decoder and the JPEG encoder each hold a copy of the frame in memory, and a phone can run out. The page warns you before starting a file over 60 MB.")
        ]
    },
    "nef-to-jpg": {
        "short": "NEF to JPG",
        "title": "Convert NEF to JPG Online - Free, No Upload | MillFile",
        "meta_desc": "Convert Nikon NEF files to full-resolution JPG in your browser. Free, no sign-up, no watermark, and the file is never uploaded to a server.",
        "h1": "Convert NEF to JPG",
        "lead": "Nikon NEF files are unreadable to most websites, printers and email clients. Drop one here and get a full-resolution JPG back, decoded on your own device - nothing is uploaded.",
        "why_title": "What a NEF needs before anyone else can open it",
        "why": [
            "Nikon writes NEF as a TIFF-based container holding sensor data, a JPEG preview, and a set of maker notes that vary by model and by compression setting. That is why NEF support is uneven: a viewer that handles a D750 file can fail on a newer body that uses high-efficiency compression. LibRaw tracks those variants, and it is the decoder running inside this page.",
            "Converting here instead of uploading means a 30 MB wedding frame never crosses the network. Our own measurement on a 26 megapixel file is roughly two to three seconds; a 45 megapixel frame takes noticeably longer and asks for more memory."
        ],
        "faq": [
            ("Does this work with high-efficiency NEF compression?",
             "Usually. LibRaw covers the compression variants Nikon has shipped, but a decoder cannot know a format that postdates it, so a brand new body may be refused. When that happens the row says failed, and the original file is untouched on your disk."),
            ("Will the colours match what I see in Nikon software?",
             "Not exactly. This page renders with the white balance recorded in the file and a standard demosaic, not Nikon's own Picture Control pipeline, so contrast and colour rendering differ slightly from NX Studio. You keep the full resolution and the highlight information; the look is a plain render."),
            ("Are the JPGs tagged with the capture date and lens?",
             "No. The JPEG is encoded from the decoded pixels, so the camera metadata does not travel with it. If you need the EXIF later, keep the NEF - this page does not modify or replace it."),
            ("What quality should I pick?",
             "Standard is the sensible default for sharing and printing. High keeps more detail at a larger file size, and Small suits email attachments and web forms where the file has to stay small.")
        ]
    },
    "arw-to-jpg": {
        "short": "ARW to JPG",
        "title": "Convert ARW to JPG Online - Free, No Upload | MillFile",
        "meta_desc": "Convert Sony ARW files to full-resolution JPG in your browser. Decoded from the sensor data, never from the embedded preview. Free, and never uploaded.",
        "h1": "Convert ARW to JPG",
        "lead": "Drop a Sony ARW file here for a full-resolution JPG. The frame is decoded in your browser, so a large file never crosses the network - no account, no watermark, no daily cap.",
        "why_title": "Why ARW files need care",
        "why": [
            "Sony stores a full-size JPEG preview inside most ARW files next to the raw data. That is why so many tools show you a picture almost instantly and then produce something different when you actually convert. This page does not take that shortcut: the frame is decoded from the sensor data, so the output matches the file rather than the preview.",
            "Sony also changes compression between camera generations, and some bodies record lossless-compressed raw that older decoders reject outright. If your file is one of those, the row says so - a failure you can see beats a JPG that quietly looks wrong."
        ],
        "faq": [
            ("Why not just use the embedded preview?",
             "Because the preview is a separate, smaller JPEG the camera generated. Using it would hand you a lower-resolution picture than the file actually contains. Decoding the sensor data takes longer and gives you the real frame."),
            ("Does it handle lossless-compressed ARW?",
             "Usually, through LibRaw. Sony has introduced new compression with recent bodies, and a decoder that predates a camera cannot know its format. Failures are reported per file rather than hidden."),
            ("How long does a 61 megapixel file take?",
             "Longer than the 26 megapixel frame we measured at two to three seconds - roughly in proportion to the pixel count. Expect several times that on a laptop, and more on a phone, where memory is the binding constraint rather than processor speed."),
            ("Do you keep a copy of my file?",
             "No. There is no upload step and no server behind this page. The file is read into this tab, decoded here, and handed back as a download link that never leaves your machine.")
        ]
    },
    "dng-to-jpg": {
        "short": "DNG to JPG",
        "title": "Convert DNG to JPG Online - Free, No Upload | MillFile",
        "meta_desc": "Convert DNG and ProRAW files to full-resolution JPG in your browser. Free, no account, no watermark, and the file is never uploaded anywhere.",
        "h1": "Convert DNG to JPG",
        "lead": "DNG is the open RAW format that phones, drones and Adobe tools write. Drop one here for a full-resolution JPG, decoded on your device - nothing leaves your machine.",
        "why_title": "What actually arrives in a DNG",
        "why": [
            "DNG was designed so a raw file could be read without reverse engineering every camera, and it worked well enough that Apple ProRAW and many Android camera apps write it. It is still raw: a JPG needs a demosaic, a white balance decision and an encode, which is what this page does, in the browser.",
            "One caveat specific to DNG. Some files, including a few phone features, store a JPEG or a lightly compressed payload rather than untouched sensor data. Those convert quickly and look fine, but they are not giving you more information than the phone had already decided on."
        ],
        "faq": [
            ("Does this work with Apple ProRAW?",
             "ProRAW is a DNG and LibRaw handles DNG, so it usually decodes. ProRAW also carries a large amount of extra processing metadata that this page does not apply, so the render is plainer than what the Photos app shows you."),
            ("Will a DNG converted here look like the Adobe version?",
             "Close, but not identical. Adobe applies its own camera profiles; this page uses the white balance recorded in the file and a standard demosaic. Expect the same picture with slightly different colour rendering."),
            ("What about DNG files that hold a JPEG instead of sensor data?",
             "They still convert, and quickly, because there is far less to decode. The output resolution can be lower than you expect, because that detail was never in the file to begin with."),
            ("Is my DNG uploaded anywhere?",
             "No. There is no upload step and no backend: the file is read into this tab, decoded here, and turned into a download you save yourself. The page loads no analytics and no third-party scripts either.")
        ]
    }
}

