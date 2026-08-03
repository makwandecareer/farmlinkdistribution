param(
  [string]$ProjectRoot = "E:\farmlink-production",
  [string]$BaseUrl = "https://www.farmlinkdistribution.co.za",
  [string]$MeasurementId = "G-1Q33161CYQ"
)

$ErrorActionPreference = "Stop"
$frontend = Join-Path $ProjectRoot "frontend"
if (-not (Test-Path (Join-Path $frontend "index.html"))) {
  throw "FarmLink frontend not found at $frontend"
}

$products = @(
  @{ Name="Eggs"; Slug="eggs"; Singular="egg"; Audience="retailers, bakeries, restaurants, caterers, hotels, wholesalers and institutions"; Specs="egg size, grading, packaging, weekly volume, delivery frequency and destination"; Intro="Bulk and recurring egg supply enquiries coordinated through approved farmers and commercial suppliers." },
  @{ Name="Poultry"; Slug="poultry"; Singular="poultry product"; Audience="retailers, restaurants, caterers, wholesalers and food-service businesses"; Specs="product type, quantity, packaging, cold-chain requirements, delivery frequency and destination"; Intro="Commercial poultry supply enquiries for approved buyers and verified agricultural suppliers." },
  @{ Name="Potatoes"; Slug="potatoes"; Singular="potato"; Audience="retailers, wholesalers, restaurants, caterers, processors and institutions"; Specs="variety, grade, bag size, order volume, delivery frequency and destination"; Intro="Bulk potato sourcing enquiries coordinated across South Africa, subject to supplier availability." },
  @{ Name="Onions"; Slug="onions"; Singular="onion"; Audience="retailers, wholesalers, restaurants, caterers, processors and institutions"; Specs="variety, grade, bag size, volume, delivery frequency and destination"; Intro="Commercial onion sourcing and distribution enquiries for business buyers." },
  @{ Name="Tomatoes"; Slug="tomatoes"; Singular="tomato"; Audience="retailers, wholesalers, restaurants, caterers, processors and institutions"; Specs="variety, grade, packaging, volume, ripeness requirements and destination"; Intro="Fresh tomato supply enquiries coordinated with suitable agricultural suppliers." },
  @{ Name="Cabbage"; Slug="cabbage"; Singular="cabbage"; Audience="retailers, wholesalers, restaurants, caterers and institutions"; Specs="head size, grade, quantity, packaging, delivery frequency and destination"; Intro="Bulk cabbage procurement enquiries for commercial and institutional buyers." },
  @{ Name="Carrots"; Slug="carrots"; Singular="carrot"; Audience="retailers, wholesalers, restaurants, caterers, processors and institutions"; Specs="grade, size, packaging, volume, washing requirements and destination"; Intro="Commercial carrot sourcing enquiries coordinated through the FarmLink network." },
  @{ Name="Spinach"; Slug="spinach"; Singular="spinach"; Audience="retailers, wholesalers, restaurants, caterers and institutions"; Specs="bunch or bulk format, grade, volume, delivery frequency and destination"; Intro="Fresh spinach procurement enquiries for business buyers across South Africa." },
  @{ Name="Maize"; Slug="maize"; Singular="maize product"; Audience="wholesalers, processors, retailers, feed businesses and institutions"; Specs="maize type, grade, moisture specification, packaging, tonnage and destination"; Intro="Commercial maize supply enquiries, subject to specification and approved supplier capacity." },
  @{ Name="Animal Feed"; Slug="animal-feed"; Singular="animal feed product"; Audience="farmers, agricultural businesses, cooperatives, retailers and distributors"; Specs="animal category, feed type, formulation, bag size, order volume and destination"; Intro="Animal-feed sourcing enquiries for farms and agricultural businesses." },
  @{ Name="Fertilizer"; Slug="fertilizer"; Singular="fertilizer product"; Audience="farmers, cooperatives, agricultural retailers and commercial growers"; Specs="crop, formulation, bag size, quantity, application requirements and destination"; Intro="Fertilizer procurement enquiries for commercial growers and agricultural businesses." },
  @{ Name="Fresh Vegetables"; Slug="fresh-vegetables"; Singular="vegetable"; Audience="retailers, wholesalers, restaurants, caterers, processors and institutions"; Specs="product list, grades, packaging, weekly volumes, delivery schedule and destination"; Intro="Multi-product fresh-vegetable sourcing enquiries from commercial and institutional buyers." },
  @{ Name="Fresh Fruit"; Slug="fresh-fruit"; Singular="fruit product"; Audience="retailers, wholesalers, hospitality businesses, caterers, processors and institutions"; Specs="fruit type, variety, grade, packaging, volume and destination"; Intro="Fresh-fruit procurement enquiries coordinated according to season and supplier availability." },
  @{ Name="Livestock"; Slug="livestock"; Singular="livestock requirement"; Audience="approved agricultural businesses, processors, traders and institutional buyers"; Specs="species, breed, age or weight range, quantity, documentation and destination"; Intro="Structured livestock sourcing enquiries subject to legal, welfare and traceability requirements." },
  @{ Name="Agricultural Inputs"; Slug="agricultural-inputs"; Singular="agricultural input"; Audience="farmers, cooperatives, agricultural retailers and commercial growers"; Specs="input category, technical specification, quantity, packaging and delivery destination"; Intro="Commercial sourcing enquiries for approved agricultural inputs and farm requirements." }
)

$productRoot = Join-Path $frontend "products"
New-Item -ItemType Directory -Force -Path $productRoot | Out-Null

$css = @'
:root{--green:#073827;--green2:#0b6b49;--gold:#c79a2b;--ink:#14221c;--muted:#65716b;--line:#dfe7e2;--bg:#f4f7f5;--white:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6}
a{color:inherit}.container{width:min(1160px,calc(100% - 32px));margin:auto}.topbar{background:var(--green);color:#fff;padding:14px 0}.topbar .container{display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:12px;text-decoration:none;font-weight:800}.brand img{width:46px;height:46px;object-fit:contain;background:#fff;border-radius:10px}.navlinks{display:flex;gap:18px;flex-wrap:wrap}.navlinks a{text-decoration:none;font-weight:700;font-size:14px}
.hero{background:linear-gradient(125deg,#073827,#0b6b49);color:#fff;padding:76px 0 64px}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-weight:900;font-size:12px;color:#f0c75a}.hero h1{font-size:clamp(36px,6vw,66px);line-height:1.04;max-width:940px;margin:12px 0 20px}.hero p{font-size:18px;max-width:780px;color:#dcebe4}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.btn{display:inline-flex;padding:13px 18px;border-radius:10px;text-decoration:none;font-weight:850}.primary{background:var(--gold);color:#112017}.secondary{border:1px solid #ffffff55;color:#fff}
.section{padding:64px 0}.section h2{font-size:clamp(28px,4vw,42px);line-height:1.15;margin:0 0 14px}.lead{color:var(--muted);max-width:820px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:0 12px 30px #0738270d}.card h3{margin:0 0 10px}.card p{color:var(--muted);margin:0}
.product-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:26px}.product-link{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;text-decoration:none;font-weight:850}.product-link:hover{border-color:var(--green2);transform:translateY(-2px)}
.steps{counter-reset:step;display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}.step{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px}.step:before{counter-increment:step;content:counter(step);display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#e8f3ed;color:var(--green);font-weight:900;margin-bottom:12px}
.cta{background:#fff;border:1px solid var(--line);border-radius:20px;padding:34px;display:flex;justify-content:space-between;align-items:center;gap:24px}.cta h2{margin-bottom:8px}.footer{background:#05291d;color:#d9e5df;padding:34px 0;margin-top:40px}.footer a{color:#fff}
.breadcrumb{font-size:13px;color:#d7e6df;margin-bottom:18px}.breadcrumb a{color:#fff}.faq{display:grid;gap:12px;margin-top:24px}.faq details{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px}.faq summary{font-weight:850;cursor:pointer}.notice{background:#fff7df;border:1px solid #ead494;border-radius:12px;padding:16px 18px;color:#665117;margin-top:22px}
@media(max-width:800px){.grid,.product-grid,.steps{grid-template-columns:1fr}.topbar .container,.cta{align-items:flex-start;flex-direction:column}.navlinks{display:none}.hero{padding:54px 0}.section{padding:46px 0}}
'@
Set-Content -LiteralPath (Join-Path $productRoot "seo.css") -Value $css -Encoding UTF8

function GoogleTag([string]$id) {
  return @"
<script async src="https://www.googletagmanager.com/gtag/js?id=$id"></script>
<script>
window.dataLayer=window.dataLayer||[];
function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());
gtag('config','$id',{'anonymize_ip':true});
</script>
"@
}

$allLinks = ($products | ForEach-Object {
  "<a class='product-link' href='$BaseUrl/products/$($_.Slug)/'>$($_.Name)</a>"
}) -join "`n"

foreach ($p in $products) {
  $dir = Join-Path $productRoot $p.Slug
  New-Item -ItemType Directory -Force -Path $dir | Out-Null

  $title = "$($p.Name) Suppliers South Africa | FarmLink Distribution"
  $description = "$($p.Intro) Submit a commercial requirement to FarmLink Distribution for supplier matching, quotation and delivery coordination."
  $canonical = "$BaseUrl/products/$($p.Slug)/"

  $schema = @{
    "@context"="https://schema.org"
    "@graph"=@(
      @{
        "@type"="Organization"
        "@id"="$BaseUrl/#organization"
        name="FarmLink Distribution"
        url="$BaseUrl/"
        logo="$BaseUrl/assets/farmlink-logo.png"
        areaServed=@{ "@type"="Country"; name="South Africa" }
      },
      @{
        "@type"="CollectionPage"
        "@id"="$canonical#webpage"
        url=$canonical
        name=$title
        description=$description
        isPartOf=@{ "@id"="$BaseUrl/#website" }
        about=@{ "@type"="Product"; name=$p.Name }
      },
      @{
        "@type"="BreadcrumbList"
        itemListElement=@(
          @{ "@type"="ListItem"; position=1; name="Home"; item="$BaseUrl/" },
          @{ "@type"="ListItem"; position=2; name="Products"; item="$BaseUrl/products/" },
          @{ "@type"="ListItem"; position=3; name=$p.Name; item=$canonical }
        )
      },
      @{
        "@type"="FAQPage"
        mainEntity=@(
          @{ "@type"="Question"; name="How do I request $($p.Name.ToLower()) supply through FarmLink?"; acceptedAnswer=@{ "@type"="Answer"; text="Submit your business details, required volume, specification, delivery location and timing through the FarmLink registration and order portal. FarmLink reviews the requirement before confirming availability and commercial terms." } },
          @{ "@type"="Question"; name="Does FarmLink guarantee $($p.Name.ToLower()) availability?"; acceptedAnswer=@{ "@type"="Answer"; text="No. Availability is confirmed only after FarmLink verifies suitable supplier capacity, specification, route and delivery timing." } },
          @{ "@type"="Question"; name="Can suppliers register to offer $($p.Name.ToLower())?"; acceptedAnswer=@{ "@type"="Answer"; text="Yes. Agricultural suppliers may submit their capacity, specifications, location and supporting commercial details for review." } }
        )
      }
    )
  } | ConvertTo-Json -Depth 12 -Compress

  $html = @"
<!doctype html>
<html lang="en-ZA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>$title</title>
<meta name="description" content="$description">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="$canonical">
<meta property="og:type" content="website">
<meta property="og:title" content="$title">
<meta property="og:description" content="$description">
<meta property="og:url" content="$canonical">
<meta property="og:image" content="$BaseUrl/assets/farmlink-logo.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="$title">
<meta name="twitter:description" content="$description">
<link rel="stylesheet" href="../seo.css">
$(GoogleTag $MeasurementId)
<script type="application/ld+json">$schema</script>
</head>
<body>
<header class="topbar">
  <div class="container">
    <a class="brand" href="$BaseUrl/"><img src="../../assets/farmlink-logo.png" alt="FarmLink Distribution"><span>FarmLink Distribution</span></a>
    <nav class="navlinks"><a href="$BaseUrl/">Home</a><a href="$BaseUrl/products/">All products</a><a href="$BaseUrl/provinces/">Provinces</a><a href="$BaseUrl/#portal">Register or order</a></nav>
  </div>
</header>
<main>
<section class="hero">
  <div class="container">
    <div class="breadcrumb"><a href="$BaseUrl/">Home</a> / <a href="$BaseUrl/products/">Products</a> / $($p.Name)</div>
    <div class="eyebrow">National agricultural sourcing</div>
    <h1>$($p.Name) suppliers in South Africa</h1>
    <p>$($p.Intro) FarmLink coordinates structured commercial enquiries for $($p.Audience).</p>
    <div class="actions"><a class="btn primary" href="$BaseUrl/#portal">Submit a supply requirement</a><a class="btn secondary" href="tel:+27774573727">Call +27 77 457 3727</a></div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="eyebrow">Commercial requirements</div>
    <h2>What buyers should specify</h2>
    <p class="lead">A complete requirement improves supplier matching and quotation accuracy. For $($p.Name.ToLower()), include $($p.Specs).</p>
    <div class="grid">
      <article class="card"><h3>Product specification</h3><p>State the required grade, type, packaging format and any technical or quality requirements.</p></article>
      <article class="card"><h3>Volume and frequency</h3><p>Provide the once-off or recurring quantity and the preferred collection or delivery schedule.</p></article>
      <article class="card"><h3>Delivery destination</h3><p>Include the town, province, receiving requirements and required delivery date.</p></article>
    </div>
    <div class="notice">Product availability, pricing and delivery are not guaranteed by this page. FarmLink confirms supply only through a written quotation or invoice after reviewing the requirement.</div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="eyebrow">Controlled workflow</div>
    <h2>How FarmLink coordinates $($p.Name.ToLower()) enquiries</h2>
    <div class="steps">
      <article class="step"><h3>Submit requirement</h3><p>Share business, product, volume and destination details.</p></article>
      <article class="step"><h3>Review specification</h3><p>FarmLink checks whether the requirement is commercially clear and feasible.</p></article>
      <article class="step"><h3>Match supply</h3><p>Suitable approved suppliers are assessed against capacity, location and specification.</p></article>
      <article class="step"><h3>Confirm transaction</h3><p>Price, payment terms, collection and delivery are documented before fulfilment.</p></article>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="eyebrow">Frequently asked questions</div>
    <h2>$($p.Name) supply enquiries</h2>
    <div class="faq">
      <details><summary>How do I request $($p.Name.ToLower()) supply?</summary><p>Submit your business details, required volume, specification, delivery location and timing through the FarmLink registration and order portal.</p></details>
      <details><summary>Does FarmLink guarantee availability?</summary><p>No. Availability is confirmed only after suitable supplier capacity, specification, route and delivery timing have been verified.</p></details>
      <details><summary>Can suppliers register?</summary><p>Yes. Agricultural suppliers may submit capacity, specifications, location and supporting commercial details for review.</p></details>
    </div>
  </div>
</section>

<section class="section">
  <div class="container"><div class="cta"><div><div class="eyebrow">Start a commercial enquiry</div><h2>Request $($p.Name.ToLower()) supply through FarmLink</h2><p class="lead">Provide a complete requirement so the team can assess suitable suppliers and routes.</p></div><a class="btn primary" href="$BaseUrl/#portal">Open registration portal</a></div></div>
</section>

<section class="section">
  <div class="container"><div class="eyebrow">Explore categories</div><h2>Other agricultural products</h2><div class="product-grid">$allLinks</div></div>
</section>
</main>
<footer class="footer"><div class="container">© 2026 FarmLink Distribution · Nationwide agricultural coordination · <a href="$BaseUrl/">www.farmlinkdistribution.co.za</a></div></footer>
</body>
</html>
"@
  Set-Content -LiteralPath (Join-Path $dir "index.html") -Value $html -Encoding UTF8
}

$productIndex = @"
<!doctype html>
<html lang="en-ZA">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agricultural Products and Suppliers South Africa | FarmLink Distribution</title>
<meta name="description" content="Explore agricultural product sourcing pages from FarmLink Distribution. Submit bulk requirements for eggs, poultry, fresh produce, maize, animal feed, fertilizer and other categories.">
<link rel="canonical" href="$BaseUrl/products/">
<link rel="stylesheet" href="seo.css">
$(GoogleTag $MeasurementId)
</head>
<body>
<header class="topbar"><div class="container"><a class="brand" href="$BaseUrl/"><img src="../assets/farmlink-logo.png" alt="FarmLink Distribution"><span>FarmLink Distribution</span></a></div></header>
<main>
<section class="hero"><div class="container"><div class="eyebrow">South Africa</div><h1>Agricultural products and supplier enquiries</h1><p>Browse commercial sourcing categories and submit a structured procurement or supplier registration requirement to FarmLink Distribution.</p><div class="actions"><a class="btn primary" href="$BaseUrl/#portal">Register or place an order</a><a class="btn secondary" href="$BaseUrl/provinces/">Browse provinces</a></div></div></section>
<section class="section"><div class="container"><h2>Product categories</h2><p class="lead">Availability and commercial terms are confirmed only after supplier capacity, specification and delivery requirements have been reviewed.</p><div class="product-grid">$allLinks</div></div></section>
</main>
<footer class="footer"><div class="container">© 2026 FarmLink Distribution</div></footer>
</body>
</html>
"@
Set-Content -LiteralPath (Join-Path $productRoot "index.html") -Value $productIndex -Encoding UTF8

# Preserve all URLs already in the sitemap and append product URLs.
$sitemapPath = Join-Path $frontend "sitemap.xml"
$existingUrls = @()
if (Test-Path $sitemapPath) {
  $raw = Get-Content -Raw -LiteralPath $sitemapPath
  $matches = [regex]::Matches($raw, "<loc>(.*?)</loc>")
  $existingUrls = $matches | ForEach-Object { $_.Groups[1].Value }
}
$newUrls = @("$BaseUrl/products/")
$newUrls += $products | ForEach-Object { "$BaseUrl/products/$($_.Slug)/" }
$allUrls = @($existingUrls + $newUrls) | Where-Object { $_ } | Sort-Object -Unique

$today = Get-Date -Format "yyyy-MM-dd"
$urlXml = ($allUrls | ForEach-Object {
  $priority = if ($_ -eq "$BaseUrl/") { "1.0" } elseif ($_ -match "/products/$|/provinces/$") { "0.9" } else { "0.8" }
  "<url><loc>$_</loc><lastmod>$today</lastmod><changefreq>weekly</changefreq><priority>$priority</priority></url>"
}) -join "`n"
$sitemap = "<?xml version=`"1.0`" encoding=`"UTF-8`"?>`n<urlset xmlns=`"http://www.sitemaps.org/schemas/sitemap/0.9`">`n$urlXml`n</urlset>"
Set-Content -LiteralPath $sitemapPath -Value $sitemap -Encoding UTF8

Write-Host ""
Write-Host "Created national product SEO pages:"
$products | ForEach-Object { Write-Host "  /products/$($_.Slug)/" }
Write-Host ""
Write-Host "Preserved existing sitemap URLs and added product pages."
Write-Host "Next:"
Write-Host "cd /d $ProjectRoot"
Write-Host "git status"
Write-Host "git add frontend\products frontend\sitemap.xml"
Write-Host "git commit -m `"Launch national agricultural product SEO pages`""
Write-Host "git push origin main"
