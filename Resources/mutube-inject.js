// Derived from Exaphis/mutube at the revision in config/mutube.env.
// Keep the userscript version fixed so local and CI packages run the same code.
(() => {
	if (document.mutube) return;
	document.mutube = true;

	var script = document.createElement("script");
	script.src =
		"https://cdn.jsdelivr.net/npm/@foxreis/tizentube@1.15.0/dist/userScript.js?v=" +
		Date.now();
	script.async = true;
	document.head.appendChild(script);

	const originalIsTypeSupported = window.MediaSource.isTypeSupported.bind(
		window.MediaSource,
	);

	window.MediaSource.isTypeSupported = (mimeType) => {
		const parts = mimeType
			.split(";")
			.map((part) => part.trim())
			.filter((part) => part);

		const filtered = parts.filter((part) => {
			return !(part.startsWith("width=") || part.startsWith("height="));
		});

		const cleaned = filtered.join("; ");
		return originalIsTypeSupported(cleaned);
	};
})();
