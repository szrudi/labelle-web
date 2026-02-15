import { useEffect, useState } from "react";

const REPO_URL = "https://github.com/szrudi/labelle-web";

export function Footer() {
  const [latestVersion, setLatestVersion] = useState<string | null>(null);

  useEffect(() => {
    fetch("https://api.github.com/repos/szrudi/labelle-web/releases/latest")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data?.tag_name) return;
        const latest = data.tag_name.replace(/^v/, "");
        if (latest !== __APP_VERSION__) {
          setLatestVersion(latest);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <footer className="mt-8 text-center text-xs text-gray-400">
      <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-gray-600">
        Labelle Web
      </a>{" "}
      v{__APP_VERSION__}
      {latestVersion && (
        <>
          {" · "}
          <a
            href={`${REPO_URL}/releases/tag/v${latestVersion}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-600"
          >
            v{latestVersion} available
          </a>
        </>
      )}
    </footer>
  );
}