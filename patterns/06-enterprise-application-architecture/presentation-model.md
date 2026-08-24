---
name: Presentation Model
slug: presentation-model
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: [Application Model, MVVM, Model-View-ViewModel]
first_described: "Fowler, martinfowler.com, 2004"
maturity: canonical
related: [observer]
incompatible_with: []
verified: 2026-08-24
---

# Presentation Model

## 1. Name, aliases, and lineage

Presentation Model was named by Martin Fowler in an article on
martinfowler.com, first published 19 July 2004, part of his eaaDev
collection rather than the original 2002 *Patterns of Enterprise
Application Architecture* book. Fowler's own opening line, quoted directly.
"Represent the state and behavior of the presentation independently of the
GUI controls used in the interface." His own "Also Known As" line, quoted
directly. "Application Model, MVVM (Model-View-ViewModel)."

The Application Model alias traces to VisualWorks Smalltalk-80
environments, per Fowler's companion overview, "GUI Architectures,"
martinfowler.com, first published 18 July 2006, a different article and a
different date from the Presentation Model page itself.

The MVVM name comes from John Gossman, a Microsoft architect for WPF and
Silverlight, in a blog post titled "Introduction to Model/View/ViewModel
pattern for building WPF apps," dated 8 October 2005. Gossman's original
post does not mention Fowler or Presentation Model by name anywhere. it
frames MVVM as "a variation of Model/View/Controller (MVC)... tailored for
modern UI development platforms." The link between the two is a later,
retrospective observation, made explicitly by Fowler himself. quoted
directly, "In the years since this pattern was written, it is increasingly
known as MVVM (Model-View-ViewModel), which uses the name 'ViewModel' to
refer to the presentation model element of the pattern." Wikipedia
additionally credits Microsoft architects Ken Cooper and Ted Peters as
co-originators alongside Gossman's announcement.

## 2. Problem and context

Conventional GUI code stores presentation state directly inside widget or
control instances, a checkbox's checked property, a textbox's text
property, and so on. This makes presentation logic hard to unit test,
because exercising it requires an instantiated, often platform-specific,
UI toolkit. it bloats view classes with both rendering and behavioral
logic combined. and it makes keeping multiple views of the same conceptual
state in sync error prone, because there is no single authoritative object
representing "what should currently be displayed" independent of the
widgets themselves.

## 3. Forces

Fowler names the central tension directly. "If you put the synchronization
in the view, it won't get picked up by tests on the Presentation Model. If
you put it in the Presentation Model you add a dependency to the view." He
calls the required synchronization "probably the most annoying part of
Presentation Model," simple to write but repetitive.

Testability without a running UI pulls toward isolating state fully in the
Presentation Model. Fowler is explicit that one Presentation Model can
drive several views at once, quoted directly. "While several views can
utilize the same Presentation Model, each view should require only one
Presentation Model."

## 4. Applicability and non-applicability

Reach for this pattern when view logic and state need to be unit tested
without a running UI toolkit, or when more than one view must present the
same underlying state consistently.

It is overkill for a single, small, throwaway screen with trivial logic,
where the added class and its synchronization code buy nothing. Modern
guidance from Microsoft's own MVVM documentation frames the payoff in terms
of growth. the pattern earns its cost as "complex maintenance issues...
arise as apps are modified and grow in size and scope," which implies the
inverse for a small, stable screen.

## 5. Structure

Presentation Model. A fully self-contained class representing all the data
and behavior of a UI window, holding no reference to any widget or view
class, and independent of the UI framework.

View. Thin, renders and projects the Presentation Model's state, and is
the only participant that knows about both the Presentation Model and the
concrete UI toolkit.

Domain Model. Sits beneath, referenced by the Presentation Model, not
directly by the View.

The awareness chain runs one way only. the View knows about the
Presentation Model, the Presentation Model knows about the Domain Model,
and the Domain Model knows about neither.

## 6. ASCII structure diagram

```
+------------------+
| Domain Model     |
+------------------+
        ^
        | (Presentation Model calls into it)
        |
+------------------------+
| Presentation Model     |
| all state and behavior |
| no reference to a view |
+------------------------+
        ^
        | (View binds to and observes it)
        |
+------------------+   +------------------+
| View A           |   | View B           |
| thin, renders    |   | thin, renders    |
+------------------+   +------------------+

Awareness runs one way. View knows the Presentation Model, the
Presentation Model knows the Domain Model, never the reverse.
```

## 7. Dynamics

A user action is captured by the View and delegated to a method or command
on the Presentation Model, never handled by calling the Domain Model
directly from the View. The Presentation Model updates its own state and,
where needed, calls into the Domain Model. Synchronization back to the
View happens either through hand-written code, Fowler's original 2004
description, or through automatic data binding, the mechanism MVVM
formalizes on top of the same structural idea.

Modern binding-capable frameworks require the Presentation Model, there
called a ViewModel, to implement a change-notification contract, `INotifyPropertyChanged`
in .NET, and raise a change event whenever a bound property changes. the
View's data-bound controls subscribe to that event and update
automatically, which is the mechanized version of what Fowler in 2004 could
only describe as repetitive, hand-written synchronization code.

## 8. Implementation variants

Presentation Model versus MVP. Fowler positions Presentation Model as an
alternative to Supervising Controller and Passive View, quoted directly.
"Presentation Model is a pattern that pulls presentation behavior from a
view. As such it's an alternative to Supervising Controller and Passive
View," adding that "Compared to Passive View and Supervising Controller,
Presentation Model allows you to write logic that is completely independent
of the views used for display." The precise structural difference from
classic MVP. an MVP Presenter typically holds a reference to the View,
usually through a View interface, so it can be tested via mocking, and the
View commonly instantiates and owns its Presenter. A pure Presentation
Model holds no reference to the View at all. the View observes or binds to
the Presentation Model, never the other way round.

Presentation Model versus MVVM. MVVM is Presentation Model's own name for
frameworks capable of first-class, two-way data binding, WPF, Silverlight,
and later XAML-based Xamarin and .NET MAUI, plus JavaScript frameworks such
as Knockout.js. Per Fowler's own account, the ViewModel element of MVVM is
simply the Presentation Model element renamed. the distinguishing detail is
mechanistic rather than conceptual. MVVM assumes a declarative binding
engine handles the synchronization work Fowler had to describe as manual in
2004, because neither WPF nor mainstream JavaScript binding libraries
existed at the time he wrote the pattern.

## 9. Known production uses

.NET, WPF, Xamarin, and .NET MAUI. Microsoft's own architecture guide
states MVVM "helps cleanly separate an application's business and
presentation logic from its user interface (UI)," and names official
first-party libraries built around it, the .NET Community MVVM Toolkit,
ReactiveUI, and the Prism Library.

Knockout.js, a JavaScript library that self-describes as part of the MVVM
family, its own documentation stating, "Developers familiar with Ruby on
Rails, ASP.NET MVC, or other MV* technologies may see MVVM as a real-time
form of MVC with declarative syntax."

Android Architecture Components `ViewModel`. Google's own official
documentation, worth stating precisely, deliberately avoids the terms
"MVVM" or "Model-View-ViewModel" anywhere. its own language is "state
holder," describing the class as one that "exposes state to the UI and
encapsulates related business logic," whose "principal advantage is that
it caches state and persists it through configuration changes." Developers
commonly use this class to build MVVM-shaped architectures, but Google
itself never applies that label to it.

## 10. Consequences

Positive. Testable presentation logic and state with no running UI
toolkit required. multiple views can share one Presentation Model. the
Model can, per Microsoft's own guidance, "evolve independently of the
view." and designers and developers can work in parallel, Microsoft's
phrasing, "Designers can focus on the view, while developers can work on
the view model and model components."

Negative. An extra class and extra indirection per screen. potential
duplication of state between the Domain Model and the Presentation Model.
and synchronization bugs, whether from hand-rolled pre-binding code or from
a missed change-notification event in a bound implementation, Microsoft's
own guidance lists explicit rules such as never raising a property-changed
event from inside a view model's constructor, itself evidence this is a
real, documented source of bugs in practice.

## 11. Failure modes and misuse

"Massive View Controller," a real, precisely sourced criticism. Ash
Furrow, objc.io, Issue 13, June 2014, writing, "Ever heard of MVC? Massive
View Controller, some call it," and framing MVVM explicitly as the fix, "an
augmented version of MVC where we formally connect the view and
controller, and move presentation logic out of the controller and into a
new object, the view model." The mirror-image criticism sometimes called
"Massive ViewModel," the same bloat relocated one layer over when
discipline is not applied, is a real and widely recognised community term
by direct analogy, but no specific, independently citable primary source
for it was confirmed in this entry's research. it is named here as a
plausible, logically consistent risk rather than presented as a directly
quoted, dated criticism.

## 12. Trade-off matrix

Grounded in Fowler's own "GUI Architectures" overview, 18 July 2006.

| Pattern | Sync mechanism | Testability | Key trade-off |
|---|---|---|---|
| MVC, classic Smalltalk | Observer synchronization, views and controllers observe the model directly | Moderate, domain independent but coupling varies | Elegant for multiple widgets updating together, implicit observer chains are hard to debug |
| Passive View, an MVP variant | None, the presenter manually pushes every value into every widget | High, the view has no logic to test | The most manual widget-manipulation code, the view is deliberately dumb |
| Supervising Controller, an MVP variant | Partial, the view handles simple bindings itself, the presenter handles complex logic | Moderate | User gestures are handed to a Supervising Controller for anything non-trivial |
| Presentation Model | State fully mirrored in a UI-independent object, the view syncs itself to it | Highest, logic is completely independent of the views used for display | Requires an explicit synchronization mechanism, manual before 2004, automatic with modern data binding |

## 13. Related and incompatible patterns

Observer underlies the whole family. Fowler notes views and controllers
"observe the model," letting "multiple widgets update without needing to
communicate directly."

Data Binding is the modern mechanization of the Presentation Model's
manual synchronization step, the mechanism that turns Presentation Model
into MVVM in practice.

MVVM is a named specialization of Presentation Model for data-binding
capable frameworks.

MVP, in both its Supervising Controller and Passive View shapes, is a
sibling alternative rather than a specialization, distinguished precisely
in dimension 8.

Application Model, VisualWorks Smalltalk, is Presentation Model's direct
historical ancestor, per Fowler's own account in "GUI Architectures."
"Widgets do not observe domain objects directly, instead they observe the
application model."

## 14. Refactoring path in and out

Extracting a Presentation Model out of view code that currently mixes
rendering and state generally proceeds by identifying state currently
stored on widget properties, lifting it into plain fields or properties on
a new, UI-independent class, replacing direct widget reads and writes in
event handlers with calls into the new class's methods, then adding the
synchronization step, manual or data bound, last. This sequence is stated
here as reasoned, standard practice, not a verbatim source quote.

Folding a Presentation Model back into its view for a genuinely trivial,
single-use screen is the mirror image, and follows the same
do-not-add-indirection-you-do-not-need judgment named in dimension 4.

## 15. Testing and verification

Testability is the pattern's primary, stated motivation. Fowler's own
words, the Presentation Model is "a fully self-contained class" testable
"without any of the controls used to render that UI." Microsoft's own
guidance states the same payoff directly. "Developers can create unit
tests for the view model and the model, without using the view. The unit
tests for the view model can exercise exactly the same functionality as
used by the view."

## 16. Observability signals

State-transition logging inside the Presentation Model or ViewModel layer,
logging every bound-property change or command invocation, is a natural
debugging aid, precisely because the object is UI-independent and
therefore easy to log without touching rendering code. This is reasoned
engineering practice rather than a source-cited claim.

## 17. Security and privacy implications

Genuinely minimal on its own. The one narrow, real concern is that a
Presentation Model or ViewModel commonly holds display-formatted copies of
domain data, so a generic logging pass over its state risks incidentally
capturing sensitive fields that were fine to keep in the domain model but
should not be duplicated into application logs once mirrored into the
presentation layer. This deserves one line of caution in a real
deployment, not a dedicated new concern.

## 18. References

1. Martin Fowler, "Presentation Model," martinfowler.com, first published
   19 July 2004. `https://martinfowler.com/eaaDev/PresentationModel.html`,
   verified 2026-08-24.
2. Martin Fowler, "GUI Architectures," martinfowler.com, first published
   18 July 2006. `https://martinfowler.com/eaaDev/uiArchs.html`, verified
   2026-08-24.
3. John Gossman, "Introduction to Model/View/ViewModel pattern for
   building WPF apps," 8 October 2005, archived by Microsoft.
   `https://learn.microsoft.com/en-us/archive/blogs/johngossman/introduction-to-modelviewviewmodel-pattern-for-building-wpf-apps`,
   verified 2026-08-24.
4. Microsoft, "MVVM (Model-View-ViewModel) architectural pattern," .NET
   MAUI documentation.
   `https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm`,
   verified 2026-08-24.
5. Knockout.js documentation, introduction.
   `https://knockoutjs.com/documentation/introduction.html`, verified
   2026-08-24.
6. Android Developers, "ViewModel overview."
   `https://developer.android.com/topic/libraries/architecture/viewmodel`,
   verified 2026-08-24.
7. Ash Furrow, "Model-View-ViewModel for iOS," objc.io, Issue 13, June
   2014. `https://www.objc.io/issues/13-architecture/mvvm/`, verified
   2026-08-24.
8. Wikipedia, "Model-view-viewmodel," consulted for the Ken Cooper and
   Ted Peters co-origination detail, verified 2026-08-24.

**Evidence grade.** high

**Most solid findings.** The Fowler origin and definition, fetched and
quoted directly from the primary martinfowler.com page. The Gossman MVVM
naming, fetched from Microsoft's own archived copy of the original post,
including the precise, honest detail that Gossman never mentions Fowler by
name. the Android ViewModel nuance, that Google's own documentation avoids
the MVVM label entirely.

**Unverified or unclear.** No specific, independently citable primary
source for a "Massive ViewModel" criticism was found, so it is presented
as a plausible, logically consistent risk rather than a dated, attributed
quote. Fowler's own explicit non-applicability guidance was not
independently retrieved in full from the live page and is presented here
via Microsoft's own framing instead.

## Code

### C#

```csharp
using System.ComponentModel;
using System.Threading.Tasks;

public interface IAuthService
{
    Task SignInAsync(string username);
}

public class LoginViewModel : INotifyPropertyChanged
{
    private string _username = string.Empty;
    private bool _isBusy;

    public string Username
    {
        get => _username;
        set { _username = value; OnPropertyChanged(nameof(Username)); }
    }

    public bool IsBusy
    {
        get => _isBusy;
        private set { _isBusy = value; OnPropertyChanged(nameof(IsBusy)); }
    }

    public async Task LoginAsync(IAuthService auth)
    {
        IsBusy = true;
        await auth.SignInAsync(Username);
        IsBusy = false;
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged(string name) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
```

### Swift

```swift
import Combine

protocol AuthService {
    func signIn(username: String) async
}

final class LoginPresentationModel: ObservableObject {
    @Published var username: String = ""
    @Published private(set) var isBusy: Bool = false

    private let auth: AuthService

    init(auth: AuthService) {
        self.auth = auth
    }

    func login() async {
        isBusy = true
        await auth.signIn(username: username)
        isBusy = false
    }
}
```

### Kotlin

```kotlin
class LoginViewModel(private val auth: AuthService) : ViewModel() {
    private val _username = MutableStateFlow("")
    val username: StateFlow<String> = _username

    private val _isBusy = MutableStateFlow(false)
    val isBusy: StateFlow<Boolean> = _isBusy

    fun setUsername(value: String) {
        _username.value = value
    }

    fun login() {
        viewModelScope.launch {
            _isBusy.value = true
            auth.signIn(_username.value)
            _isBusy.value = false
        }
    }
}
```

### TypeScript

```typescript
interface AuthService {
  signIn(username: string): Promise<void>;
}

class LoginPresentationModel {
  private listeners: Array<() => void> = [];
  username = "";
  isBusy = false;

  onChange(listener: () => void): void {
    this.listeners.push(listener);
  }

  private notify(): void {
    for (const listener of this.listeners) listener();
  }

  setUsername(value: string): void {
    this.username = value;
    this.notify();
  }

  async login(auth: AuthService): Promise<void> {
    this.isBusy = true;
    this.notify();
    await auth.signIn(this.username);
    this.isBusy = false;
    this.notify();
  }
}
```

### Python

```python
class LoginPresentationModel:
    def __init__(self, auth_service):
        self._auth = auth_service
        self._listeners = []
        self.username = ""
        self.is_busy = False

    def on_change(self, listener):
        self._listeners.append(listener)

    def _notify(self):
        for listener in self._listeners:
            listener()

    def set_username(self, value):
        self.username = value
        self._notify()

    def login(self):
        self.is_busy = True
        self._notify()
        self._auth.sign_in(self.username)
        self.is_busy = False
        self._notify()
```
