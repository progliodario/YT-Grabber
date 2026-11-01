#!/bin/sh
# Builds the signed apt and dnf repositories and the landing page that GitHub Pages publishes.
#   usage: build_repos.sh ASSETS_DIR SITE_DIR KEY_FINGERPRINT
# ASSETS_DIR holds the .deb and the (already signed) .rpm of the release. Needs: apt-ftparchive, createrepo_c, gpg.
set -eu
ASSETS="$1"
SITE="$2"
FPR="$3"
BASE="https://progliodario.github.io/YT-Grabber"

rm -rf "$SITE"
mkdir -p "$SITE/apt/pool/main" "$SITE/rpm"
cp "$ASSETS"/yt-grabber_*_all.deb "$SITE/apt/pool/main/"
cp "$ASSETS"/yt-grabber-*.noarch.rpm "$SITE/rpm/"
gpg --export "$FPR" > "$SITE/yt-grabber.gpg"
gpg --export --armor "$FPR" > "$SITE/yt-grabber.asc"

# ---- apt: the package is architecture "all", so every architecture lists the same file
( cd "$SITE/apt"
  for arch in amd64 arm64 armhf; do
    dir="dists/stable/main/binary-$arch"
    mkdir -p "$dir"
    apt-ftparchive packages pool > "$dir/Packages"
    gzip -9kf "$dir/Packages"
  done
  apt-ftparchive \
    -o APT::FTPArchive::Release::Origin="YT Grabber" \
    -o APT::FTPArchive::Release::Label="YT Grabber" \
    -o APT::FTPArchive::Release::Suite=stable \
    -o APT::FTPArchive::Release::Codename=stable \
    -o APT::FTPArchive::Release::Architectures="amd64 arm64 armhf" \
    -o APT::FTPArchive::Release::Components=main \
    release dists/stable > dists/stable/Release.new
  mv dists/stable/Release.new dists/stable/Release
  gpg --batch --yes --local-user "$FPR" --armor --detach-sign --output dists/stable/Release.gpg dists/stable/Release
  gpg --batch --yes --local-user "$FPR" --clearsign --output dists/stable/InRelease dists/stable/Release
)

# ---- dnf
createrepo_c "$SITE/rpm"
gpg --batch --yes --local-user "$FPR" --armor --detach-sign --output "$SITE/rpm/repodata/repomd.xml.asc" "$SITE/rpm/repodata/repomd.xml"
cat > "$SITE/yt-grabber.repo" <<EOF
[yt-grabber]
name=YT Grabber
baseurl=$BASE/rpm
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=$BASE/yt-grabber.asc
EOF

# ---- landing page
cat > "$SITE/index.html" <<EOF
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>YT Grabber packages (apt and dnf)</title>
<style>
:root{--bg:#fff;--fg:#14172a;--muted:#4b5268;--code:#eef0f6;--link:#1d3fb8;--focus:#b02d44}
@media (prefers-color-scheme:dark){:root{--bg:#10131c;--fg:#eceef6;--muted:#b4bacb;--code:#1c2130;--link:#9db4ff;--focus:#fc728c}}
body{margin:0;background:var(--bg);color:var(--fg);font:1rem/1.6 system-ui,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:46rem;margin:0 auto;padding:1.5rem 1rem 3rem}
a{color:var(--link)}
a:focus-visible,pre:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.skip{position:absolute;left:.5rem;top:-4rem;background:var(--fg);color:var(--bg);padding:.6rem 1rem;border-radius:6px}
.skip:focus{top:.5rem}
pre{background:var(--code);padding:1rem;overflow:auto;border-radius:8px;font:.9rem/1.5 ui-monospace,Consolas,Menlo,monospace}
code{font:.9rem ui-monospace,Consolas,Menlo,monospace;overflow-wrap:anywhere}
.muted{color:var(--muted)}
</style>
</head><body>
<a class="skip" href="#main">Skip to the main content</a>
<div class="wrap">
<header><p class="muted"><a href="https://github.com/progliodario/YT-Grabber">YT Grabber on GitHub</a></p></header>
<main id="main">
<h1>YT Grabber packages</h1>
<p>Signed apt and dnf repositories for <a href="https://github.com/progliodario/YT-Grabber">YT Grabber</a>. Updates arrive with the normal system updates.</p>
<h2 id="apt">Debian, Ubuntu, Linux Mint, Raspberry Pi OS</h2>
<pre tabindex="0" aria-labelledby="apt">sudo install -d /etc/apt/keyrings
curl -fsSL $BASE/yt-grabber.gpg | sudo tee /etc/apt/keyrings/yt-grabber.gpg &gt; /dev/null
echo "deb [signed-by=/etc/apt/keyrings/yt-grabber.gpg] $BASE/apt stable main" | sudo tee /etc/apt/sources.list.d/yt-grabber.list
sudo apt update &amp;&amp; sudo apt install yt-grabber</pre>
<h2 id="dnf">Fedora, RHEL, Rocky, Alma, openSUSE</h2>
<pre tabindex="0" aria-labelledby="dnf">sudo curl -fsSL -o /etc/yum.repos.d/yt-grabber.repo $BASE/yt-grabber.repo
sudo dnf install yt-grabber</pre>
<h2>Check the signature</h2>
<p>Signing key fingerprint: <code>$FPR</code>. The public key is <a href="yt-grabber.asc">yt-grabber.asc</a>.</p>
</main>
<footer><p class="muted">Accessibility of YT Grabber itself: <a href="https://github.com/progliodario/YT-Grabber/blob/main/docs/accessibility.md">accessibility statement</a>.</p></footer>
</div>
</body></html>
EOF
touch "$SITE/.nojekyll"
echo "Repositories built in $SITE"
