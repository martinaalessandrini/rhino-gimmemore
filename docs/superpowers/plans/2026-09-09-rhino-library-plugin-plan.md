# Rhino Library Plugin - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Rhino 7/8 plugin with a dockable Eto.Forms panel for browsing, searching, and importing 3D interior design models from a local folder-based library.

**Architecture:** C# .NET Rhino plugin with Eto.Forms UI, JSON index caching, in-memory keyword search with tokenization, and Rhino-native thumbnail generation. The library is organized hierarchically: Category/SubCategory/Brand/Model files, and the plugin auto-generates a `library.json` index with stale detection.

**Tech Stack:** C#, .NET 6+ (targeting Rhino 8), RhinoCommon SDK, Eto.Forms (bundled with Rhino), System.Text.Json

**Spec:** `docs/superpowers/specs/2026-09-09-rhino-library-plugin-design.md`

## Global Constraints

- Plugin runs inside Rhino 7/8 as a .NET assembly.
- UI must use Eto.Forms (Rhino's cross-platform UI toolkit).
- Library root path is user-configurable and persisted via Rhino plugin settings.
- All file paths support Unicode and long paths.
- Thumbnails are optional: if missing or generation fails, show a placeholder.
- `.3ds` import depends on the 3ds importer plugin being installed in Rhino (default in Rhino).
- Stale detection: compare `lastScanned` in `library.json` against the most recent file modification time in the library folder tree.

---

## File Structure

```
RhinoLibraryPlugin/
├── RhinoLibraryPlugin.csproj
├── Plugin.cs                          // Entry point: Rhino.PlugIns.PlugIn subclass
├── Commands/
│   └── ShowLibraryPanelCommand.cs     // Rhino command to show the dockable panel
├── Core/
│   ├── ModelEntry.cs                  // Data model for a library item
│   ├── LibraryIndex.cs                // JSON-serializable index container (entries + lastScanned)
│   ├── LibreriaEngine.cs              // Folder scanning, index persistence, stale detection
│   └── SearchEngine.cs                // Query normalization, tokenization, filtering
├── Services/
│   ├── ThumbnailManager.cs            // Check existing thumbs, generate via Rhino temp doc
│   └── ImportManager.cs               // Import file into current RhinoDoc
├── UI/
│   └── LibraryPanel.cs                // Eto.Forms dockable panel with search, filters, grid
├── Settings/
│   └── PluginSettings.cs              // Persist LibraryRootPath, AutoGenerateThumbnails, ThumbnailSize
└── Tests/
    ├── Core.Tests.csproj
    ├── LibreriaEngineTests.cs
    └── SearchEngineTests.cs
```

---

## Task 1: Scaffolding and Core Data Models

**Files:**
- Create: `RhinoLibraryPlugin/RhinoLibraryPlugin.csproj`
- Create: `RhinoLibraryPlugin/Plugin.cs`
- Create: `RhinoLibraryPlugin/Core/ModelEntry.cs`
- Create: `RhinoLibraryPlugin/Core/LibraryIndex.cs`

**Interfaces:**
- Produces: `ModelEntry` class with properties: `FilePath`, `Category`, `SubCategory`, `Brand`, `ModelName`, `Format`, `ThumbnailPath`
- Produces: `LibraryIndex` class with `LastScanned` (DateTime) and `Entries` (List&lt;ModelEntry&gt;)

- [ ] **Step 1: Create project file**

Create `RhinoLibraryPlugin/RhinoLibraryPlugin.csproj` targeting .NET 6 (for Rhino 8):

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0-windows</TargetFramework>
    <UseWPF>false</UseWPF>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
    <AppendTargetFrameworkToOutputPath>false</AppendTargetFrameworkToOutputPath>
    <RhinoPluginType>gp</RhinoPluginType>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="RhinoCommon" Version="8.0.0" />
  </ItemGroup>
</Project>
```

- [ ] **Step 2: Create plugin entry point**

Create `RhinoLibraryPlugin/Plugin.cs`:

```csharp
using Rhino.PlugIns;

namespace RhinoLibraryPlugin
{
    public class RhinoLibraryPlugin : PlugIn
    {
        public static RhinoLibraryPlugin Instance { get; private set; }

        public RhinoLibraryPlugin()
        {
            Instance = this;
        }

        protected override LoadReturnCode OnLoad(ref string errorMessage)
        {
            return LoadReturnCode.Success;
        }
    }
}
```

- [ ] **Step 3: Create ModelEntry data model**

Create `RhinoLibraryPlugin/Core/ModelEntry.cs`:

```csharp
namespace RhinoLibraryPlugin.Core
{
    public class ModelEntry
    {
        public string FilePath { get; set; }
        public string Category { get; set; }
        public string SubCategory { get; set; }
        public string Brand { get; set; }
        public string ModelName { get; set; }
        public string Format { get; set; }
        public string ThumbnailPath { get; set; }
    }
}
```

- [ ] **Step 4: Create LibraryIndex container**

Create `RhinoLibraryPlugin/Core/LibraryIndex.cs`:

```csharp
using System;
using System.Collections.Generic;

namespace RhinoLibraryPlugin.Core
{
    public class LibraryIndex
    {
        public DateTime LastScanned { get; set; }
        public List<ModelEntry> Entries { get; set; } = new List<ModelEntry>();
    }
}
```

- [ ] **Step 5: Build to verify**

Run: `dotnet build RhinoLibraryPlugin/RhinoLibraryPlugin.csproj`
Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add RhinoLibraryPlugin/
git commit -m "feat: scaffold project, ModelEntry, and LibraryIndex"
```

---

## Task 2: LibreriaEngine - Folder Scanning and Index Persistence

**Files:**
- Create: `RhinoLibraryPlugin/Core/LibreriaEngine.cs`
- Modify: `RhinoLibraryPlugin/Plugin.cs` (add instance property)

**Interfaces:**
- Consumes: `ModelEntry`, `LibraryIndex`
- Produces: `LibreriaEngine.ScanLibrary(string rootPath) → List<ModelEntry>`
- Produces: `LibreriaEngine.LoadIndex(string rootPath) → LibraryIndex`
- Produces: `LibreriaEngine.SaveIndex(string rootPath, LibraryIndex index)`
- Produces: `LibreriaEngine.IsIndexStale(string rootPath, DateTime lastScanned) → bool`
- Produces: `LibreriaEngine.GetCategories(List<ModelEntry>) → List<string>`
- Produces: `LibreriaEngine.GetSubCategories(List<ModelEntry>, string category) → List<string>`
- Produces: `LibreriaEngine.GetBrands(List<ModelEntry>, string category, string subCategory) → List<string>`

- [ ] **Step 1: Write failing test for ScanLibrary**

Create `Tests/LibreriaEngineTests.cs`:

```csharp
using System;
using System.IO;
using System.Linq;
using RhinoLibraryPlugin.Core;
using Xunit;

namespace RhinoLibraryPlugin.Tests
{
    public class LibreriaEngineTests : IDisposable
    {
        private readonly string _testDir;

        public LibreriaEngineTests()
        {
            _testDir = Path.Combine(Path.GetTempPath(), $"LibTest_{Guid.NewGuid()}");
            Directory.CreateDirectory(_testDir);
            // Create test structure: Arredi/Letti/Poliform/LettoBaba.obj
            var brandDir = Path.Combine(_testDir, "Arredi", "Letti", "Poliform");
            Directory.CreateDirectory(brandDir);
            File.WriteAllText(Path.Combine(brandDir, "LettoBaba.obj"), "dummy");
        }

        public void Dispose()
        {
            if (Directory.Exists(_testDir))
                Directory.Delete(_testDir, recursive: true);
        }

        [Fact]
        public void ScanLibrary_CreatesCorrectModelEntry()
        {
            var engine = new LibreriaEngine();
            var entries = engine.ScanLibrary(_testDir);

            Assert.Single(entries);
            var entry = entries[0];
            Assert.Equal("Arredi", entry.Category);
            Assert.Equal("Letti", entry.SubCategory);
            Assert.Equal("Poliform", entry.Brand);
            Assert.Equal("LettoBaba", entry.ModelName);
            Assert.Equal(".obj", entry.Format);
        }

        [Fact]
        public void SaveAndLoadIndex_RoundTrip()
        {
            var engine = new LibreriaEngine();
            var entries = engine.ScanLibrary(_testDir);
            engine.SaveIndex(_testDir, new LibraryIndex { LastScanned = DateTime.UtcNow, Entries = entries });

            var loaded = engine.LoadIndex(_testDir);
            Assert.Single(loaded.Entries);
            Assert.Equal("LettoBaba", loaded.Entries[0].ModelName);
        }
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `dotnet test Tests/Core.Tests.csproj --filter "FullyQualifiedName~LibreriaEngineTests" -v n`
Expected: FAIL — `LibreriaEngine` class not found.

- [ ] **Step 3: Implement LibreriaEngine**

Create `RhinoLibraryPlugin/Core/LibreriaEngine.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace RhinoLibraryPlugin.Core
{
    public class LibreriaEngine
    {
        private static readonly string[] SupportedFormats = { ".obj", ".3ds", ".3dm" };
        private const string IndexFileName = "library.json";

        public List<ModelEntry> ScanLibrary(string rootPath)
        {
            var entries = new List<ModelEntry>();
            if (!Directory.Exists(rootPath))
                return entries;

            foreach (var categoryDir in Directory.EnumerateDirectories(rootPath))
            {
                string category = Path.GetFileName(categoryDir);
                foreach (var subCategoryDir in Directory.EnumerateDirectories(categoryDir))
                {
                    string subCategory = Path.GetFileName(subCategoryDir);
                    foreach (var brandDir in Directory.EnumerateDirectories(subCategoryDir))
                    {
                        string brand = Path.GetFileName(brandDir);
                        foreach (var filePath in Directory.EnumerateFiles(brandDir))
                        {
                            string ext = Path.GetExtension(filePath).ToLowerInvariant();
                            if (!SupportedFormats.Contains(ext))
                                continue;

                            string modelName = Path.GetFileNameWithoutExtension(filePath);
                            string thumbPath = Path.Combine(brandDir, $"{modelName}.thumb.png");

                            entries.Add(new ModelEntry
                            {
                                FilePath = filePath,
                                Category = category,
                                SubCategory = subCategory,
                                Brand = brand,
                                ModelName = modelName,
                                Format = ext,
                                ThumbnailPath = File.Exists(thumbPath) ? thumbPath : null
                            });
                        }
                    }
                }
            }
            return entries;
        }

        public void SaveIndex(string rootPath, LibraryIndex index)
        {
            string indexPath = Path.Combine(rootPath, IndexFileName);
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(indexPath, JsonSerializer.Serialize(index, options));
        }

        public LibraryIndex LoadIndex(string rootPath)
        {
            string indexPath = Path.Combine(rootPath, IndexFileName);
            if (!File.Exists(indexPath))
                return null;

            try
            {
                string json = File.ReadAllText(indexPath);
                return JsonSerializer.Deserialize<LibraryIndex>(json);
            }
            catch
            {
                return null; // corrupted index -> regenerate
            }
        }

        public bool IsIndexStale(string rootPath, DateTime lastScanned)
        {
            if (!Directory.Exists(rootPath))
                return true;

            DateTime maxWriteTime = DateTime.MinValue;
            foreach (var file in Directory.EnumerateFiles(rootPath, "*.*", SearchOption.AllDirectories))
            {
                var writeTime = File.GetLastWriteTimeUtc(file);
                if (writeTime > maxWriteTime)
                    maxWriteTime = writeTime;
            }
            return maxWriteTime > lastScanned;
        }

        public List<string> GetCategories(List<ModelEntry> entries)
        {
            return entries.Select(e => e.Category).Distinct().OrderBy(c => c).ToList();
        }

        public List<string> GetSubCategories(List<ModelEntry> entries, string category)
        {
            return entries.Where(e => e.Category == category)
                          .Select(e => e.SubCategory)
                          .Distinct()
                          .OrderBy(s => s)
                          .ToList();
        }

        public List<string> GetBrands(List<ModelEntry> entries, string category, string subCategory)
        {
            return entries.Where(e => e.Category == category && e.SubCategory == subCategory)
                          .Select(e => e.Brand)
                          .Distinct()
                          .OrderBy(b => b)
                          .ToList();
        }
    }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `dotnet test Tests/Core.Tests.csproj --filter "FullyQualifiedName~LibreriaEngineTests" -v n`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add RhinoLibraryPlugin/Core/LibreriaEngine.cs Tests/LibreriaEngineTests.cs
git commit -m "feat: add LibreriaEngine with scan, save/load index, and stale detection"
```

---

## Task 3: SearchEngine - Query Normalization and Filtering

**Files:**
- Create: `RhinoLibraryPlugin/Core/SearchEngine.cs`
- Create: `Tests/SearchEngineTests.cs`

**Interfaces:**
- Consumes: `ModelEntry` list
- Produces: `SearchEngine.Search(string query, List<ModelEntry> entries) → List<ModelEntry>`
- Produces: `SearchEngine.NormalizeQuery(string query) → string[]`

- [ ] **Step 1: Write failing tests for SearchEngine**

Create `Tests/SearchEngineTests.cs`:

```csharp
using System.Collections.Generic;
using System.Linq;
using RhinoLibraryPlugin.Core;
using Xunit;

namespace RhinoLibraryPlugin.Tests
{
    public class SearchEngineTests
    {
        private List<ModelEntry> GetSampleEntries()
        {
            return new List<ModelEntry>
            {
                new ModelEntry { Category = "Arredi", SubCategory = "Letti", Brand = "Poliform", ModelName = "LettoBaba" },
                new ModelEntry { Category = "Arredi", SubCategory = "Comodini", Brand = "Kartell", ModelName = "ComodinoGhost" },
                new ModelEntry { Category = "Illuminazione", SubCategory = "Lampade da terra", Brand = "Flos", ModelName = "Arco" },
                new ModelEntry { Category = "Arredi", SubCategory = "Letti", Brand = "Flou", ModelName = "LettoNathalie" },
            };
        }

        [Fact]
        public void Search_Letto_ReturnsTwoBeds()
        {
            var engine = new SearchEngine();
            var results = engine.Search("letto", GetSampleEntries());
            Assert.Equal(2, results.Count);
        }

        [Fact]
        public void Search_LettoPoliform_ReturnsOne()
        {
            var engine = new SearchEngine();
            var results = engine.Search("letto poliform", GetSampleEntries());
            Assert.Single(results);
            Assert.Equal("LettoBaba", results[0].ModelName);
        }

        [Fact]
        public void Search_WithHyphens_Normalizes()
        {
            var engine = new SearchEngine();
            var results = engine.Search("letto-poliform", GetSampleEntries());
            Assert.Single(results);
        }

        [Fact]
        public void Search_NoMatch_ReturnsEmpty()
        {
            var engine = new SearchEngine();
            var results = engine.Search("tavolo", GetSampleEntries());
            Assert.Empty(results);
        }

        [Fact]
        public void Search_CaseInsensitive()
        {
            var engine = new SearchEngine();
            var results = engine.Search("POLIFORM", GetSampleEntries());
            Assert.Single(results);
            Assert.Equal("LettoBaba", results[0].ModelName);
        }
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `dotnet test Tests/Core.Tests.csproj --filter "FullyQualifiedName~SearchEngineTests" -v n`
Expected: FAIL — `SearchEngine` not found.

- [ ] **Step 3: Implement SearchEngine**

Create `RhinoLibraryPlugin/Core/SearchEngine.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

namespace RhinoLibraryPlugin.Core
{
    public class SearchEngine
    {
        public string[] NormalizeQuery(string query)
        {
            if (string.IsNullOrWhiteSpace(query))
                return Array.Empty<string>();

            var normalized = query.ToLowerInvariant()
                                   .Replace("-", " ")
                                   .Replace("_", " ")
                                   .Replace("  ", " ");
            return normalized.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
        }

        public List<ModelEntry> Search(string query, List<ModelEntry> entries)
        {
            var tokens = NormalizeQuery(query);
            if (tokens.Length == 0)
                return entries.ToList();

            var results = new List<ModelEntry>();
            foreach (var entry in entries)
            {
                string searchable = $"{entry.Category} {entry.SubCategory} {entry.Brand} {entry.ModelName}".ToLowerInvariant();
                if (tokens.All(token => searchable.Contains(token)))
                {
                    results.Add(entry);
                }
            }

            // Sort: matches in model name or brand come first
            return results.OrderByDescending(e =>
            {
                string modelNameLower = e.ModelName.ToLowerInvariant();
                string brandLower = e.Brand.ToLowerInvariant();
                int score = 0;
                foreach (var token in tokens)
                {
                    if (modelNameLower.Contains(token)) score += 10;
                    else if (brandLower.Contains(token)) score += 5;
                    else score += 1;
                }
                return score;
            }).ThenBy(e => e.ModelName).ToList();
        }
    }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `dotnet test Tests/Core.Tests.csproj --filter "FullyQualifiedName~SearchEngineTests" -v n`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add RhinoLibraryPlugin/Core/SearchEngine.cs Tests/SearchEngineTests.cs
git commit -m "feat: add SearchEngine with query normalization and token-based filtering"
```

---

## Task 4: PluginSettings - Persist User Preferences

**Files:**
- Create: `RhinoLibraryPlugin/Settings/PluginSettings.cs`

**Interfaces:**
- Produces: `PluginSettings.LibraryRootPath` (string, get/set)
- Produces: `PluginSettings.AutoGenerateThumbnails` (bool, get/set, default true)
- Produces: `PluginSettings.ThumbnailSize` (int, get/set, default 128)
- Produces: `PluginSettings.Save()` and `PluginSettings.Load()` methods

- [ ] **Step 1: Implement PluginSettings**

Create `RhinoLibraryPlugin/Settings/PluginSettings.cs`:

```csharp
using Rhino;

namespace RhinoLibraryPlugin.Settings
{
    public class PluginSettings
    {
        private const string RootPathKey = "LibraryRootPath";
        private const string AutoThumbKey = "AutoGenerateThumbnails";
        private const string ThumbSizeKey = "ThumbnailSize";

        public string LibraryRootPath
        {
            get => Rhino.PlugIns.PlugIn.GetPluginSettings(RootPathKey) as string ?? string.Empty;
            set => Rhino.PlugIns.PlugIn.SetPluginSettings(RootPathKey, value);
        }

        public bool AutoGenerateThumbnails
        {
            get
            {
                var val = Rhino.PlugIns.PlugIn.GetPluginSettings(AutoThumbKey);
                return val is bool b ? b : true;
            }
            set => Rhino.PlugIns.PlugIn.SetPluginSettings(AutoThumbKey, value);
        }

        public int ThumbnailSize
        {
            get
            {
                var val = Rhino.PlugIns.PlugIn.GetPluginSettings(ThumbSizeKey);
                return val is int i ? i : 128;
            }
            set => Rhino.PlugIns.PlugIn.SetPluginSettings(ThumbSizeKey, value);
        }
    }
}
```

Note: `Rhino.PlugIns.PlugIn.GetPluginSettings`/`SetPluginSettings` may need adjustment based on actual RhinoCommon API. Alternative: use a simple JSON file in `%APPDATA%/RhinoLibraryPlugin/settings.json`. If the Rhino settings API is not available as static methods, store settings on the `RhinoLibraryPlugin` instance or use a JSON file.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/Settings/PluginSettings.cs
git commit -m "feat: add PluginSettings for persisting user preferences"
```

---

## Task 5: ThumbnailManager - Check and Generate Thumbnails

**Files:**
- Create: `RhinoLibraryPlugin/Services/ThumbnailManager.cs`

**Interfaces:**
- Consumes: `ModelEntry`, `PluginSettings`
- Produces: `ThumbnailManager.GetThumbnailPath(ModelEntry entry) → string`
- Produces: `ThumbnailManager.GenerateThumbnailAsync(ModelEntry entry) → Task<string>`

- [ ] **Step 1: Implement ThumbnailManager**

Create `RhinoLibraryPlugin/Services/ThumbnailManager.cs`:

```csharp
using System;
using System.IO;
using System.Threading.Tasks;
using Rhino;
using Rhino.DocObjects;
using Rhino.FileIO;
using RhinoLibraryPlugin.Core;
using RhinoLibraryPlugin.Settings;

namespace RhinoLibraryPlugin.Services
{
    public class ThumbnailManager
    {
        private readonly PluginSettings _settings;

        public ThumbnailManager(PluginSettings settings)
        {
            _settings = settings;
        }

        public string GetThumbnailPath(ModelEntry entry)
        {
            if (!string.IsNullOrEmpty(entry.ThumbnailPath) && File.Exists(entry.ThumbnailPath))
                return entry.ThumbnailPath;

            string defaultThumb = Path.Combine(
                Path.GetDirectoryName(entry.FilePath),
                $"{entry.ModelName}.thumb.png"
            );
            return File.Exists(defaultThumb) ? defaultThumb : null;
        }

        public async Task<string> GenerateThumbnailAsync(ModelEntry entry)
        {
            if (!_settings.AutoGenerateThumbnails)
                return null;

            string thumbPath = Path.Combine(
                Path.GetDirectoryName(entry.FilePath),
                $"{entry.ModelName}.thumb.png"
            );

            if (File.Exists(thumbPath))
                return thumbPath;

            return await Task.Run(() =>
            {
                try
                {
                    using (var doc = new Rhino.RhinoDoc())
                    {
                        var readOptions = new FileReadOptions
                        {
                            ImportMode = true
                        };
                        bool success = doc.ReadFile(entry.FilePath, readOptions);
                        if (!success)
                            return null;

                        // Use the first view or create one
                        var view = doc.Views.Count > 0 ? doc.Views[0] : doc.Views.Add("Thumbnail", Rhino.Display.DefinedViewProjection.Perspective);
                        if (view == null)
                            return null;

                        // Capture thumbnail bitmap
                        var bitmap = view.CaptureToBitmap(
                            new System.Drawing.Size(_settings.ThumbnailSize, _settings.ThumbnailSize),
                            Rhino.Display.CaptureMode.Opaque
                        );
                        if (bitmap == null)
                            return null;

                        bitmap.Save(thumbPath, System.Drawing.Imaging.ImageFormat.Png);
                        bitmap.Dispose();
                        return thumbPath;
                    }
                }
                catch
                {
                    return null;
                }
            });
        }
    }
}
```

Note: The exact Rhino API signatures (`RhinoDoc` constructor, `FileReadOptions`, `CaptureToBitmap` overloads) should be verified against RhinoCommon SDK documentation. The code above assumes Rhino 8 API.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/Services/ThumbnailManager.cs
git commit -m "feat: add ThumbnailManager with async generation and placeholder fallback"
```

---

## Task 6: ImportManager - Import Models into Rhino

**Files:**
- Create: `RhinoLibraryPlugin/Services/ImportManager.cs`

**Interfaces:**
- Produces: `ImportManager.ImportModel(string filePath) → bool`

- [ ] **Step 1: Implement ImportManager**

Create `RhinoLibraryPlugin/Services/ImportManager.cs`:

```csharp
using System;
using System.IO;
using Rhino;

namespace RhinoLibraryPlugin.Services
{
    public class ImportManager
    {
        private static readonly string[] SupportedFormats = { ".obj", ".3ds", ".3dm" };

        public bool CanImport(string filePath)
        {
            if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
                return false;
            string ext = Path.GetExtension(filePath).ToLowerInvariant();
            return Array.Exists(SupportedFormats, s => s == ext);
        }

        public bool ImportModel(string filePath)
        {
            if (!CanImport(filePath))
                return false;

            try
            {
                var doc = RhinoDoc.ActiveDoc;
                if (doc == null)
                    return false;

                // Use Rhino script command for reliable import
                string command = $"_-Import \"{filePath}\" _Enter";
                return RhinoApp.RunScript(command, false);
            }
            catch
            {
                return false;
            }
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/Services/ImportManager.cs
git commit -m "feat: add ImportManager for importing OBJ, 3DS, and 3DM files into Rhino"
```

---

## Task 7: ShowLibraryPanelCommand - Rhino Command to Open Panel

**Files:**
- Create: `RhinoLibraryPlugin/Commands/ShowLibraryPanelCommand.cs`
- Modify: `RhinoLibraryPlugin/Plugin.cs` (register panel)

**Interfaces:**
- Produces: `ShowLibraryPanelCommand` — Rhino command ID for showing the panel

- [ ] **Step 1: Create the command**

Create `RhinoLibraryPlugin/Commands/ShowLibraryPanelCommand.cs`:

```csharp
using System;
using Rhino;
using Rhino.Commands;
using RhinoLibraryPlugin.UI;
using Eto.Forms;

namespace RhinoLibraryPlugin.Commands
{
    public class ShowLibraryPanelCommand : Command
    {
        public override string EnglishName => "ShowLibraryPanel";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            var panel = Panels.GetPanel&lt;LibraryPanel&gt;(RhinoLibraryPlugin.Instance);
            if (panel != null)
            {
                Panels.OpenPanel(panel.Id);
            }
            return Result.Success;
        }
    }
}
```

- [ ] **Step 2: Register panel in Plugin.cs**

Modify `RhinoLibraryPlugin/Plugin.cs`:

```csharp
using Rhino.PlugIns;
using RhinoLibraryPlugin.UI;
using Rhino.UI;

namespace RhinoLibraryPlugin
{
    public class RhinoLibraryPlugin : PlugIn
    {
        public static RhinoLibraryPlugin Instance { get; private set; }

        public RhinoLibraryPlugin()
        {
            Instance = this;
        }

        protected override LoadReturnCode OnLoad(ref string errorMessage)
        {
            // Register the dockable panel
            Panels.RegisterPanel(this, typeof(LibraryPanel), "Libreria Interni", Properties.Resources.LibraryIcon);
            return LoadReturnCode.Success;
        }
    }
}
```

Note: `Properties.Resources.LibraryIcon` assumes an embedded icon resource. If not available, use `null` or a temporary icon.

- [ ] **Step 3: Commit**

```bash
git add RhinoLibraryPlugin/Commands/ShowLibraryPanelCommand.cs RhinoLibraryPlugin/Plugin.cs
git commit -m "feat: add ShowLibraryPanelCommand and register dockable panel"
```

---

## Task 8: LibraryPanel - Eto.Forms Dockable UI

**Files:**
- Create: `RhinoLibraryPlugin/UI/LibraryPanel.cs`

**Interfaces:**
- Consumes: `LibreriaEngine`, `SearchEngine`, `ThumbnailManager`, `ImportManager`, `PluginSettings`
- Produces: `LibraryPanel` — Eto.Forms dockable panel with search bar, cascading filters, result grid, import button, and refresh button.

- [ ] **Step 1: Implement LibraryPanel**

Create `RhinoLibraryPlugin/UI/LibraryPanel.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Eto.Forms;
using Rhino;
using RhinoLibraryPlugin.Core;
using RhinoLibraryPlugin.Services;
using RhinoLibraryPlugin.Settings;
using Rhino.UI;

namespace RhinoLibraryPlugin.UI
{
    public class LibraryPanel : Panel, IPanel
    {
        private readonly PluginSettings _settings;
        private readonly LibreriaEngine _libEngine;
        private readonly SearchEngine _searchEngine;
        private readonly ThumbnailManager _thumbManager;
        private readonly ImportManager _importManager;

        private List<ModelEntry> _allEntries = new List<ModelEntry>();
        private List<ModelEntry> _filteredEntries = new List<ModelEntry>();

        private TextBox _searchBox;
        private DropDown _categoryDropDown;
        private DropDown _subCategoryDropDown;
        private DropDown _brandDropDown;
        private GridView _resultsGrid;
        private Button _refreshButton;
        private Label _statusLabel;

        public LibraryPanel()
        {
            _settings = new PluginSettings();
            _libEngine = new LibreriaEngine();
            _searchEngine = new SearchEngine();
            _thumbManager = new ThumbnailManager(_settings);
            _importManager = new ImportManager();

            BuildLayout();
            LoadLibraryAsync();
        }

        private void BuildLayout()
        {
            _searchBox = new TextBox { PlaceholderText = "Cerca per categoria, marca, modello..." };
            _searchBox.TextChanged += OnSearchTextChanged;

            _categoryDropDown = new DropDown { Enabled = false };
            _categoryDropDown.SelectedIndexChanged += OnFilterChanged;

            _subCategoryDropDown = new DropDown { Enabled = false };
            _subCategoryDropDown.SelectedIndexChanged += OnFilterChanged;

            _brandDropDown = new DropDown { Enabled = false };
            _brandDropDown.SelectedIndexChanged += OnFilterChanged;

            var filterLayout = new DynamicLayout();
            filterLayout.BeginHorizontal();
            filterLayout.Add(_categoryDropDown, true);
            filterLayout.Add(_subCategoryDropDown, true);
            filterLayout.Add(_brandDropDown, true);
            filterLayout.EndHorizontal();

            _resultsGrid = new GridView();
            SetupResultsGrid();

            _refreshButton = new Button { Text = "Aggiorna libreria" };
            _refreshButton.Click += (s, e) => LoadLibraryAsync();

            _statusLabel = new Label { Text = "Caricamento..." };

            var bottomLayout = new DynamicLayout();
            bottomLayout.BeginHorizontal();
            bottomLayout.Add(_refreshButton);
            bottomLayout.Add(_statusLabel, true);
            bottomLayout.EndHorizontal();

            var mainLayout = new DynamicLayout();
            mainLayout.BeginVertical();
            mainLayout.Add(_searchBox);
            mainLayout.Add(filterLayout);
            mainLayout.Add(_resultsGrid, true);
            mainLayout.Add(bottomLayout);
            mainLayout.EndVertical();

            Content = mainLayout;
        }

        private void SetupResultsGrid()
        {
            _resultsGrid.Columns.Add(new GridColumn
            {
                HeaderText = "Nome",
                DataCell = new TextBoxCell("ModelName")
            });
            _resultsGrid.Columns.Add(new GridColumn
            {
                HeaderText = "Marca",
                DataCell = new TextBoxCell("Brand")
            });
            _resultsGrid.Columns.Add(new GridColumn
            {
                HeaderText = "Formato",
                DataCell = new TextBoxCell("Format")
            });

            // Import button column
            var importButtonColumn = new GridColumn
            {
                HeaderText = "Azione",
                DataCell = new CustomCell
                {
                    CreateCell = args =>
                    {
                        var entry = args.Item as ModelEntry;
                        var btn = new Button { Text = "Importa" };
                        btn.Click += (s, e) => ImportEntry(entry);
                        return btn;
                    }
                }
            };
            _resultsGrid.Columns.Add(importButtonColumn);
        }

        private async void LoadLibraryAsync()
        {
            _statusLabel.Text = "Caricamento libreria...";
            string rootPath = _settings.LibraryRootPath;
            if (string.IsNullOrEmpty(rootPath) || !System.IO.Directory.Exists(rootPath))
            {
                _statusLabel.Text = "Seleziona la cartella libreria nelle impostazioni del plugin";
                return;
            }

            await Task.Run(() =>
            {
                var index = _libEngine.LoadIndex(rootPath);
                if (index == null || _libEngine.IsIndexStale(rootPath, index.LastScanned))
                {
                    var entries = _libEngine.ScanLibrary(rootPath);
                    index = new LibraryIndex { LastScanned = DateTime.UtcNow, Entries = entries };
                    _libEngine.SaveIndex(rootPath, index);
                }
                _allEntries = index.Entries;
            });

            PopulateFilterDropDowns();
            ApplyFiltersAndSearch();
            _statusLabel.Text = $"{_allEntries.Count} oggetti trovati";
        }

        private void PopulateFilterDropDowns()
        {
            var categories = _libEngine.GetCategories(_allEntries);
            _categoryDropDown.Items.Clear();
            _categoryDropDown.Items.Add("Tutte le categorie");
            foreach (var cat in categories)
                _categoryDropDown.Items.Add(cat);
            _categoryDropDown.SelectedIndex = 0;
            _categoryDropDown.Enabled = true;
        }

        private void OnFilterChanged(object sender, EventArgs e)
        {
            // Update cascading dropdowns
            string selectedCategory = _categoryDropDown.SelectedIndex > 0 ? _categoryDropDown.SelectedValue as string : null;
            string selectedSubCategory = _subCategoryDropDown.SelectedIndex > 0 ? _subCategoryDropDown.SelectedValue as string : null;

            if (sender == _categoryDropDown)
            {
                var subCategories = _libEngine.GetSubCategories(_allEntries, selectedCategory ?? "");
                _subCategoryDropDown.Items.Clear();
                _subCategoryDropDown.Items.Add("Tutte le sottocategorie");
                foreach (var sub in subCategories)
                    _subCategoryDropDown.Items.Add(sub);
                _subCategoryDropDown.SelectedIndex = 0;
                _subCategoryDropDown.Enabled = true;

                _brandDropDown.Items.Clear();
                _brandDropDown.Enabled = false;
            }
            else if (sender == _subCategoryDropDown)
            {
                var brands = _libEngine.GetBrands(_allEntries, selectedCategory ?? "", selectedSubCategory ?? "");
                _brandDropDown.Items.Clear();
                _brandDropDown.Items.Add("Tutte le marche");
                foreach (var brand in brands)
                    _brandDropDown.Items.Add(brand);
                _brandDropDown.SelectedIndex = 0;
                _brandDropDown.Enabled = true;
            }

            ApplyFiltersAndSearch();
        }

        private void OnSearchTextChanged(object sender, EventArgs e)
        {
            ApplyFiltersAndSearch();
        }

        private void ApplyFiltersAndSearch()
        {
            var pool = _allEntries.AsEnumerable();

            // Apply cascading filters
            if (_categoryDropDown.SelectedIndex > 0)
                pool = pool.Where(e => e.Category == (_categoryDropDown.SelectedValue as string));
            if (_subCategoryDropDown.SelectedIndex > 0)
                pool = pool.Where(e => e.SubCategory == (_subCategoryDropDown.SelectedValue as string));
            if (_brandDropDown.SelectedIndex > 0)
                pool = pool.Where(e => e.Brand == (_brandDropDown.SelectedValue as string));

            // Apply text search
            string query = _searchBox.Text;
            if (!string.IsNullOrWhiteSpace(query))
                pool = _searchEngine.Search(query, pool.ToList()).AsEnumerable();

            _filteredEntries = pool.ToList();
            _resultsGrid.DataStore = _filteredEntries;

            if (_filteredEntries.Count == 0)
                _statusLabel.Text = "Nessun risultato trovato";
            else
                _statusLabel.Text = $"{_filteredEntries.Count} risultati";
        }

        private void ImportEntry(ModelEntry entry)
        {
            if (entry == null)
                return;

            bool success = _importManager.ImportModel(entry.FilePath);
            if (success)
                RhinoApp.WriteLine($"Importato: {entry.ModelName}");
            else
                RhinoApp.WriteLine($"Errore importazione: {entry.ModelName}");
        }

        // IPanel implementation
        public Guid PanelId => new Guid("YOUR-GUID-HERE-1234-567890ABCDEF");
        public void HidePanel() { }
        public void ShowPanel() { }
    }
}
```

Note: Replace `YOUR-GUID-HERE-1234-567890ABCDEF` with a real GUID generated via `guidgen` or `New-Guid`. Also, `CustomCell` syntax and `GridView` column setup may need adjustment based on Eto.Forms version shipped with Rhino 8.

- [ ] **Step 2: Commit**

```bash
git add RhinoLibraryPlugin/UI/LibraryPanel.cs
git commit -m "feat: add LibraryPanel Eto.Forms UI with search, filters, grid, and import"
```

---

## Task 9: Wiring and Final Integration

**Files:**
- Modify: `RhinoLibraryPlugin/Plugin.cs` (ensure panel registration and settings initialization)
- Modify: `RhinoLibraryPlugin/RhinoLibraryPlugin.csproj` (add references)

- [ ] **Step 1: Update .csproj with all files**

Ensure `RhinoLibraryPlugin.csproj` includes all source files and references:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0-windows</TargetFramework>
    <UseWPF>false</UseWPF>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
    <AppendTargetFrameworkToOutputPath>false</AppendTargetFrameworkToOutputPath>
    <RhinoPluginType>gp</RhinoPluginType>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="RhinoCommon" Version="8.0.0" />
  </ItemGroup>
  <ItemGroup>
    <Compile Include="Commands\ShowLibraryPanelCommand.cs" />
    <Compile Include="Core\LibreriaEngine.cs" />
    <Compile Include="Core\LibraryIndex.cs" />
    <Compile Include="Core\ModelEntry.cs" />
    <Compile Include="Core\SearchEngine.cs" />
    <Compile Include="Services\ImportManager.cs" />
    <Compile Include="Services\ThumbnailManager.cs" />
    <Compile Include="Settings\PluginSettings.cs" />
    <Compile Include="UI\LibraryPanel.cs" />
    <Compile Include="Plugin.cs" />
  </ItemGroup>
</Project>
```

- [ ] **Step 2: Verify full build**

Run: `dotnet build RhinoLibraryPlugin/RhinoLibraryPlugin.csproj`
Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add RhinoLibraryPlugin/
git commit -m "feat: integrate all components, finalize plugin wiring"
```

---

## Task 10: Manual Testing and Thumbnail Background Generation

**Files:**
- Modify: `RhinoLibraryPlugin/UI/LibraryPanel.cs` (add thumbnail background loading)

- [ ] **Step 1: Add background thumbnail loading in LibraryPanel**

Modify `LibraryPanel.cs` — in the `SetupResultsGrid` method, add a `ImageViewCell` for thumbnails that loads asynchronously:

```csharp
_resultsGrid.Columns.Insert(0, new GridColumn
{
    HeaderText = "Anteprima",
    DataCell = new CustomCell
    {
        CreateCell = args =>
        {
            var imageView = new ImageView { Width = 64, Height = 64 };
            var entry = args.Item as ModelEntry;
            if (entry != null)
            {
                // Check existing thumbnail
                string thumbPath = _thumbManager.GetThumbnailPath(entry);
                if (thumbPath != null)
                {
                    imageView.Image = new Bitmap(thumbPath);
                }
                else
                {
                    // Show placeholder and generate in background
                    imageView.Image = CreatePlaceholderImage();
                    _ = Task.Run(async () =>
                    {
                        var generatedPath = await _thumbManager.GenerateThumbnailAsync(entry);
                        if (generatedPath != null)
                        {
                            await Application.Instance.InvokeAsync(() =>
                            {
                                imageView.Image = new Bitmap(generatedPath);
                            });
                        }
                    });
                }
            }
            return imageView;
        }
    }
});
```

Add helper method in `LibraryPanel`:

```csharp
private Bitmap CreatePlaceholderImage()
{
    // Create a simple gray placeholder bitmap
    var bitmap = new Bitmap(64, 64, PixelFormat.Format32bppRgb);
    using (var g = new Graphics(bitmap))
    {
        g.Clear(Color.Gray);
        g.DrawString("3D", new Font("Arial", 12), Brushes.White, 16, 20);
    }
    return bitmap;
}
```

Note: The exact Eto.Forms `CustomCell` API and `Graphics` API may differ; verify against Eto.Forms shipped with Rhino 8.

- [ ] **Step 2: Final build and commit**

Run: `dotnet build RhinoLibraryPlugin/RhinoLibraryPlugin.csproj`
Expected: Build succeeds.

```bash
git add RhinoLibraryPlugin/UI/LibraryPanel.cs
git commit -m "feat: add background thumbnail generation and placeholder images"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Section | Plan Task | Status |
|--------------|-----------|--------|
| Folder hierarchy scanning (Category/SubCategory/Brand) | Task 2 | ✅ |
| JSON index persistence (`library.json`) | Task 2 | ✅ |
| Stale detection | Task 2 | ✅ |
| Search normalization and tokenization | Task 3 | ✅ |
| Thumbnail generation (optional, background) | Task 5, Task 10 | ✅ |
| Import via Rhino APIs | Task 6 | ✅ |
| Eto.Forms dockable panel with search + filters + grid | Task 8 | ✅ |
| Plugin settings (root path, auto-thumbnail, size) | Task 4 | ✅ |
| Rhino command to show panel | Task 7 | ✅ |

### 2. Placeholder Scan
- No "TBD", "TODO", or "implement later" found.
- All test code is explicit with expected inputs/outputs.
- No vague error handling descriptions — actual try/catch blocks are shown.

### 3. Type Consistency
- `ModelEntry` properties match across all tasks.
- `LibreriaEngine` method signatures consistent between Task 2 and Task 8.
- `SearchEngine` uses `List<ModelEntry>` consistently.

### 4. Known Risks / Need Verification
- **RhinoCommon API exact signatures**: `RhinoDoc` constructor, `FileReadOptions`, `View.CaptureToBitmap`, `Panels.RegisterPanel`, `PlugIn.GetPluginSettings` may differ between Rhino 7 and 8. Implementer must verify against installed RhinoCommon SDK.
- **Eto.Forms version**: `CustomCell`, `GridView` column APIs, and `ImageView` may have slight differences. Test in Rhino 8.
- **.NET target**: Plan uses `net6.0-windows` for Rhino 8. If targeting Rhino 7, switch to `net48` and ensure Eto.Forms references are correct.
- **GUID**: PanelId GUID in `LibraryPanel.cs` must be replaced with a real unique GUID.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-09-09-rhino-library-plugin-plan.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Ogni task viene eseguito e verificato singolarmente prima di passare al successivo.

**2. Inline Execution** — Eseguo i task direttamente in questa sessione, in batch con checkpoint per revisione.

**Quale approccio preferisci?**
