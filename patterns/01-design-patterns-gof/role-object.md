---
name: Role Object
slug: role-object
family: 01-design-patterns-gof
category: Structural
aliases: []
first_described: "Dirk Baeumer, Dirk Riehle, Wolf Siberski, and Martina Wulf, Role Object, in Neil Harrison, Brian Foote, Hans Rohnert (editors), Pattern Languages of Program Design 4, Addison-Wesley, 2000, Chapter 2, pages 15 to 32. First presented as a conference paper at PLoP 97 (1997), Technical Report WUCS-97-34, Washington University Department of Computer Science."
maturity: established
related: [extension-object, decorator, adapter]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Role Object's intent, stated here before its history: model context specific views of a key abstraction as separate role objects, dynamically attached to and removed from a shared core object at runtime, so that the core interface stays small while each client sees exactly the extension it needs, and the whole aggregate is still treated as one logical object.

The pattern was written by Dirk Baeumer, Dirk Riehle, Wolf Siberski, and Martina Wulf. It first appeared as a conference paper at PLoP 97, the 1997 Pattern Languages of Programs conference organized by the Hillside Group, under the title "The Role Object Pattern" (paper 2.1, 10 pages, also archived as Technical Report WUCS-97-34, Washington University Department of Computer Science). The paper's own footer records "Copyright 1997, D. Baeumer, D. Riehle, W. Siberski, and M. Wulf," with a PDF creation date of 11 August 1997. Every PLoP submission is worked through with an assigned shepherd before the conference's writers' workshop, and the paper's own Acknowledgments name theirs directly: "We would like to thank our sheperd Ari Schoenfeld for help improving the pattern in presentation and content."

The paper was substantially revised and republished, under the shortened title "Role Object," as Chapter 2 of Pattern Languages of Program Design 4 (PLoPD4), edited by Neil Harrison, Brian Foote, and Hans Rohnert, Addison-Wesley, 2000, pages 15 to 32. Dirk Riehle's own research-archive page for the 1997 paper links forward to the 2000 chapter under the anchor text "newer revised version," and the 2000 page links back to the 1997 paper under "earlier conference paper," so the lineage is confirmed from both ends by the authors' own site. The 2000 edition is the authoritative, final text and is what this entry quotes throughout; two genuine wording differences between the two editions are called out below where they matter.

This is not one of the 23 patterns from Gamma, Helm, Johnson, and Vlissides' 1994 Design Patterns. It sits in this family because it uses that book's own template (Intent, Also Known As, Motivation, Applicability, Structure, Participants, Collaborations, Consequences, Implementation, Sample Code, Known Uses, Related Patterns), the same GoF-style idiom the family's other post-1994 PLoP entries (Extension Object, Twin, Servant) already follow. Both editions of the paper carry an explicit "ALSO KNOWN AS" heading with nothing written under it, so the primary source lists zero aliases; none are asserted here.

There is no dedicated Wikipedia article for Role Object. A search of en.wikipedia.org for "Role Object pattern" returns "The page 'Role Object pattern' does not exist," and the adjacent Wikipedia articles that discuss roles as a general object-oriented idea (Role-oriented programming, Data, context and interaction, Mixin) do not mention Baeumer, Riehle, Siberski, Wulf, PLoP, or this pattern by name.

## 2. Problem and context

A single key abstraction is used from more than one context, and each context needs its own, different view of it. The paper's own worked example: a bank has a `Customer` class serving the investment department, holding the state that department needs (name, address, savings and deposit accounts). The loan department later also needs to work with customers, but as borrowers, needing credit and security-account state the original `Customer` class was never built to hold.

Two obvious fixes both fail. Folding every department's fields and methods directly into one `Customer` class produces, in the paper's own words, "key abstractions with bloated interfaces. Such interfaces are difficult to understand and hard to maintain. Unanticipated changes cannot be handled gracefully and will trigger lots of recompilation. Changes to a client-specific part of the class interface are likely to affect clients in other subsystems or applications as well." Splitting each context into its own subclass (`Investor`, `Borrower`) breaks object identity, and the paper names the cost precisely: "From an object identity point of view, subclassing implies that two objects of different subclasses are not identical. Thus, a customer acting both as an investor and as a borrower is represented by two different objects with distinct identities... we will inevitably run into problems in case of polymorphic searches, for example when we want to make up the list of all customers in the system. The same Customer object will appear repeatedly unless we take care of eliminating 'duplicates.'"

The pattern's own resolution, quoted directly from the 2000 edition: "The Role Object pattern models context-specific views of an object as separate role objects which are dynamically attached to and removed from the core object. The resulting object aggregate represents one logical object, even though it consists of several physically distinct objects." The 1997 conference edition phrases the same idea slightly differently and introduces vocabulary later dropped: "The Role Object pattern suggests to model context-specific views of an object as separate role objects which are dynamically attached to and removed from the core object. We call the resulting composite object structure, consisting of the core and its role objects, a subject."

## 3. Forces

The template's own instructions treat forces as engineering judgement layered on top of sourced fact, not a citation itself; what follows is judgement grounded directly in the paper's own Consequences and Motivation text, which state the trade openly rather than smoothing it over.

- Interface conciseness versus context-specific extensibility. The paper's first stated advantage: "The key abstraction can be defined concisely. The Component interface is well-focussed on the essential state and behavior of the modeled key abstraction and is not bloated by context-specific role interfaces." The cost is that any client wanting a role-specific operation must go through an extra query step rather than call it directly on the core.
- Static type safety versus runtime flexibility. The Applicability section names dynamic, on-demand role attachment as a direct reason to reach for the pattern, over "fixing them statically at compile-time." The paper states the resulting liability just as directly: "Constraints on roles cannot be enforced by the type system... With the Role Object pattern, you can't rely on the type system to enforce the constraints for you. You will have to use runtime checks instead."
- Decoupling across applications versus added client complexity. Advantage, quoted: "Applications get better decoupled. By explicitly separating the Component interface from its roles, the coupling of applications based on different role extensions is decreased." Cost, quoted from the same section: "Clients are likely to get more complex. Working with an object through one of its ConcreteRole interfaces implies slight coding overhead compared to using the interface provided by the Component interface itself. A client has to check whether the object plays the role in question."
- Avoiding subclass explosion versus cross-role consistency. Advantage: "Combinatorial explosion of classes through multiple inheritance is avoided." Cost, from the 2000 edition: "Since the logical object consists of several objects which are mutually dependent, maintaining constraints and preserving the overall consistency might become difficult."
- Object identity itself becomes a design cost, not only a design benefit. The 2000 edition adds this as its own, distinct disadvantage: "More complex object identity. Role objects introduce a logical identity next to the physical identity of objects... you have to be able to ask whether it is physically identical with another role (same object), and whether it is logical identical with another role (which may be another role of the same logical object)... you have to introduce a dedicated operation."

The pattern openly favors decoupling, a concise core interface, and runtime flexibility, and it openly gives up compile-time enforcement of role composition rules and a simple, single-reference notion of object identity. Neither trade is hidden by its own authors.

## 4. Applicability and non-applicability

Quoted directly from the 2000, PLoPD4 edition:

> "Use the Role Object pattern if
>
> - you want to handle a key abstraction in different contexts, each of which might be its own application, and you do not want to put the resulting context-specific interfaces into the same class interface.
> - you want to handle the available roles dynamically so that they can be attached and removed on demand, that is at runtime, rather than fixing them statically at compile-time.
> - you want to keep role/client pairs independent from each other so that changes to a role do not affect clients that are not interested in that role.
>
> Don't use this pattern if
>
> - your [candidate] roles have strong interdependencies."

The 1997 conference edition carries a fourth applicability bullet not present in the 2000 revision, sitting between the "dynamically... at runtime" bullet and the "role/client pairs independent" bullet: "...you want to treat the extensions transparently and need to preserve the logical object identity of the resulting object conglomerate..." This is a genuine, verified textual difference between the two editions; its content is arguably folded into the Related Patterns and Implementation discussion of Decorator in the 2000 text, but the bullet itself was dropped.

Both editions add, immediately after the "don't use" line: "There are several design variations on using roles. Fowler presents a guide on these variations and shows when to use which pattern [Fowler97]." That guide is discussed under dimension 13, and it independently corroborates when Role Object is the right choice versus a lighter, static alternative.

## 5. Structure

Quoted directly from the paper's own Participants section, identical in substance between the 1997 and 2000 editions:

> "Component (Customer)
>
> - models a particular key abstraction by defining its interface;
> - specifies the protocol for adding, removing, testing and querying for role objects. A Client supplies a specification for a ConcreteRole subclass. In the simplest case, it is identified by a string.
>
> ComponentCore (CustomerCore)
>
> - implements the Component interface including the role management protocol;
> - creates ConcreteRole instances;
> - manages its role objects.
>
> ComponentRole (CustomerRole)
>
> - stores a reference to the decorated ComponentCore;
> - implements the Component interface by forwarding requests to its core attribute.
>
> ConcreteRole (Investor, Borrower)
>
> - models and implements a context-specific extension of the Component interface;
> - can be instantiated with a ComponentCore as argument."

The paper's own Collaborations section, quoted directly, describes how core and role objects work together.

> "ComponentRole forwards requests to its ComponentCore object.
>
> ComponentCore instantiates and manages ConcreteRoles."

It describes the client's side of the interaction the same way, quoted directly.

> "A client can add new roles to the core object. [In doing so], it describes the desired roles with specification objects.
>
> Whenever the client wants to work on a core object in a role specific way, he asks the core object for this role. If the core object is currently playing the requested role, it is returned to the client.
>
> If the core object does not know about a specific requested role, an exception is thrown or an error is reported."

The paper draws its own line against Decorator directly in its Implementation section: "For all context-specific roles that might extend the Component's functionality, we introduce the abstract superclass ComponentRole. ComponentRole implements the Component's interface too, but only by forwarding operation invocations to the core object. Thus, roles transparently wrap the core. ConcreteRole classes must inherit from ComponentRole. At first glance, this looks similar to the Decorator pattern. But there are several differences: Multiple roles are not chained together; each role is wrapping its core directly. Roles typically do not extend the implementation of the component operations; they just forward the request to the core." The implementation is stated as a deliberate composition of two other named patterns: "For transparent extension, we use the Decorator pattern [Gamma+95]. For creating and managing roles, we apply the Product Trader pattern [Baeumer+97]. Thus, the Role Object pattern combines two well-known patterns thereby adding new semantics."

## 6. ASCII structure diagram

Transcribed from the paper's own Figure 3, "Structure diagram of the Role Object pattern," identical in both editions.

```
                            +-----------------------------+
   ClientA -----------------|          Component            |
   ClientB -----------------+-----------------------------+
                            | operation()                    |
                            | addRole(Spec)                  |
                            | hasRole(Spec)                  |
                            | removeRole(Spec)               |
                            | getRole(Spec)                  |
                            +---------------+---------------+
                                            |
                       +--------------------+--------------------+
                       |                                         |
           +-----------------------+               +-----------------------+
           |     ComponentCore       |<--roles-------|     ComponentRole       |
           +-----------------------+----core-------->+-----------------------+
           | operation()              |               | operation()              | --> core->operation()
           | addRole(Spec)             |               | addRole(Spec)             |
           | hasRole(Spec)             |               | hasRole(Spec)             | --> core->hasRole(aSpec)
           | removeRole(Spec)          |               | removeRole(Spec)          |
           | getRole(Spec)             |               | getRole(Spec)             |
           | state                     |               +-----------+-------------+
           +-----------------------+                            |
                                                    +------------+------------+
                                                    |                         |
                                        +---------------------+   +---------------------+
                                        |    ConcreteRoleA       |   |    ConcreteRoleB       |
                                        +---------------------+   +---------------------+
                                        | addedBehaviorA()        |   | addedBehaviorB()        |
                                        | addedStateA              |   |                          |
                                        +---------------------+   +---------------------+
```

`Component` is the abstract interface both `ComponentCore` and the abstract `ComponentRole` implement. `ComponentCore` holds a `roles` collection of its currently attached role objects; each `ComponentRole` holds a `core` back-reference to the single core it wraps. `ConcreteRoleA` and `ConcreteRoleB` inherit from `ComponentRole` and add their own role-specific behavior and state. The two annotation call-outs on the diagram itself, `core->operation()` and `core->hasRole(aSpec)`, show `ComponentRole` forwarding every request it receives straight through to its `core`.

## 7. Dynamics

The paper does not carry a section titled "Dynamics," but its Motivation walkthrough plus the Collaborations text describe the runtime flow precisely. Quoted directly:

> "A client like the loan application may either work with objects of the CustomerCore class, using the interface class Customer, or with objects of concrete CustomerRole subclasses. Suppose the loan application knows a particular Customer instance through its Customer interface. The loan application may want to check whether the Customer object plays the role of Borrower. [So] it calls hasRole() with a suitable role specification. For the purpose of our example, let's assume we can name roles with a simple string. If the Customer object can play the role named 'Borrower,' the loan application will ask it to return a reference to the corresponding object. The loan application may now use this reference to call Borrower-specific operations."

And the general runtime protocol, from Implementation: "Role instances are used to decorate a core object at run-time. A key issue is how a ConcreteRole instance is actually created and attached to the core object. Notice that ConcreteRoles are not meant to be created by clients. Rather, the role creation process should be initiated by ComponentCore, thereby avoiding that role objects may exist of their own (i.e. independently of a core object). This also prevents clients from knowing how to instantiate role objects." On failure, both editions state: "If the core object does not know about a specific requested role, an exception is thrown or an error is reported."

The paper's dynamic object diagram (Figure 2) shows one `aCustomerCore` holding a `roles` collection pointing at two concrete instances, `aBorrower` and `anInvestor`, each holding a `core` back-reference to the same `aCustomerCore`. The 2000 edition additionally shows, in Figures 5 and 6, that the pattern applies recursively: `Person`, via `PersonCore`/`PersonRole`, gains a `Customer` role, and `Customer` in turn becomes its own `Component`, with `Borrower`/`Investor` as its roles. At runtime this produces a chain, `aPersonCore` to `aCustomerCore` to `aBorrower`, which the authors state enforces a role-level precondition for free: "The role level constraints are simply enforced by role objects for Borrower or Investor not coming into existence unless the Customer role already exists." This recursive-composition material was not confirmed present in the 1997 conference edition; it appears to be new to the 2000 revision.

## 8. Implementation variants

The paper's own C++ sample gives an abstract `Customer` interface declaring both domain operations and the role-management protocol (`getRole`, `addRole`, `removeRole`, `hasRole`), a `CustomerCore` privately holding `map<string, CustomerRole*> roles`, and an abstract `CustomerRole` that forwards every `Customer` operation to `core`. Role specification is a bare string equal to the concrete role class's own name; the paper directs the reader to its own Product Trader pattern for managing that lookup table. Client code down-casts explicitly:

```cpp
Customer * aCustomer = Database::load("John Doe");
Borrower * aBorrower = dynamic_cast<Borrower *>(aCustomer->getRole("Borrower"));
if (aBorrower != NULL) { /* access securities */ }
```

The iluwatar/java-design-patterns catalogue ships a real `role-object` module following the same worked example (`Customer`, `CustomerCore`, `CustomerRole`, `BorrowerRole`, `InvestorRole`) with three verified, citable divergences from the paper's own described mechanics.

First, type-safe role retrieval, closing the exact gap the C++ sample leaves open. `CustomerCore` implements `getRole` as `Optional.ofNullable(roles.get(role)).filter(expectedRole::isInstance).map(expectedRole::cast)`, taking both a role key and a `Class<T>` token so the compiler infers and checks the return type, and `Optional` forces the caller to handle absence explicitly rather than compare a raw pointer against null. This is the same generic-token fix the sibling Extension Object entry documents for Eclipse's `IAdaptable.getAdapter(Class<T>)`.

Second, role specification is an `enum`, not a bare string. `Role.java` defines `enum Role { BORROWER(BorrowerRole.class), INVESTOR(InvestorRole.class); }`, each constant carrying the concrete role class to instantiate, and each `Role.instance()` reflectively calls the class's declared constructor. This sidesteps the paper's own named risk of colliding string specification names without going as far as the paper's own suggested alternative of Type Objects, and it is a lighter substitute for the paper's own Product Trader, appropriate when the set of roles is small and known at compile time.

Third, and structurally the most significant divergence: the iluwatar code uses inheritance, not composition. `CustomerRole extends CustomerCore`, and `BorrowerRole extends CustomerRole`, so a `BorrowerRole` instance IS-A `CustomerCore` and carries its own, separate `roles` map rather than a `core` back-reference to the shared instance that actually owns it. No `core` field exists anywhere in the classes. This means the iluwatar implementation does not demonstrate the paper's own "transparently wraps its core" forwarding mechanic at all; it demonstrates a different, inheritance-based way of giving a role class the base interface's method signatures. Whoever reaches for this catalogue entry as a reference should read it as a variant on the theme, not as a faithful implementation of the transparent-decorator structure described above.

Martin Fowler's own contemporaneous paper independently confirms the decorator-based shape is a recognized, named variation, and cites the same primary authors for it: "A useful variation on this pattern is to make the role objects decorators of the core object. This means that a client who uses only the features of employee person can deal with a single object and not need to know about the use of role objects. The cost is that when ever the interface of person changes, all the roles need to be updated. See [Baeumer et al] for more details on how to do this." Nothing found ties Ruby's instance-level `Object#extend` or JavaScript's prototype and mixin idioms to Role Object by name; the structural parallel (both attach role-specific behavior to one already-live object identity at runtime) is real but no primary or secondary source connects the two, so it is not asserted as a known implementation of this pattern.

## 9. Known production uses

The primary source's own Known Uses section names two systems this entry treats as production evidence, quoted directly.

The GEBOS banking system: "The GEBOS series of object-oriented banking projects makes extensive use of this pattern [Baeumer+97a]. It provides software support for a number of banking business sections including the teller, loan, and investment department as well as self-service and account management. The GEBOS system is based on a common business domain layer modeling the bank's core concepts. Concrete workplace applications extend these core concepts using the Role Object pattern." The citation [Baeumer+97a] is Dirk Baeumer, Guido Gryczan, Rolf Knoll, Carola Lilienthal, Dirk Riehle, and Heinz Zuellighoven, "Framework Development for Large Systems," Communications of the ACM 40, no. 10 (October 1997), pages 52 to 59, confirmed to exist with this exact author list, venue, volume, and issue via Dirk Riehle's own current publication list, and its own abstract page confirms it discusses "large scale industrial banking projects."

Abstract syntax tree node decoration: "An unrelated use of the Role Object pattern is the decoration of nodes in abstract syntax trees (AST's)... Mitsui et al. discuss the use of the pattern in the context of a C++ programming environment [Mitsui+93]." The citation is Kin'ichi Mitsui, Hiroaki Nakamura, Theodore C. Law, and Shahram Javey, "Design of an Integrated and Extensible C++ Programming Environment," Object Technology for Advanced Software (ISOTAS-93, LNCS-742), Springer-Verlag, 1993, pages 95 to 109.

The paper also names the Tools and Materials framework as an earlier, less concise exploration of the same design space, and points out that others solved the same problem with a different pattern: "Schoenfeld discusses several examples, for example Person and its roles in the context of document centered business processes [Schoenfeld96]." A modern, open-source, independently checkable implementation exists too, the iluwatar/java-design-patterns `role-object` module discussed above, though its own README's list of "real-world applications" (user permission systems, game character roles, workflow task assignment) names no specific system and is not used here as a named production use, only as evidence the pattern is still catalogued and implemented today.

## 10. Consequences

Positive, quoted directly from the paper's own Consequences section across both editions.

- "The key abstraction can be defined concisely. The Component interface is well-focussed on the essential state and behavior of the modeled key abstraction and is not bloated by context-specific role interfaces."
- "Applications get better decoupled. By explicitly separating the Component interface from its roles, the coupling of applications based on different role extensions is decreased."
- "Combinatorial explosion of classes through multiple inheritance is avoided. The pattern avoids the combinatorial explosion of classes as it would result from using multiple inheritance to compose the different roles in a single class."
- "Only those objects that are needed in a given situation are actually created," since a role is instantiated only once a client actually requests it, never speculatively for every possible context.

Negative, quoted directly from the same section.

- "Clients are likely to get more complex. Working with an object through one of its ConcreteRole interfaces implies slight coding overhead compared to using the interface provided by the Component interface itself. A client has to check whether the object plays the role in question."
- "Constraints on roles cannot be enforced by the type system... you can't rely on the type system to enforce the constraints for you. You will have to use runtime checks instead."
- "Maintaining constraints between roles becomes difficult. Since a subject consists of several objects which are mutually dependent, maintaining constraints and preserving the overall subject consistency might become difficult" (1997 wording; the 2000 edition keeps the same claim without the word "subject": "Since the logical object consists of several objects which are mutually dependent, maintaining constraints and preserving the overall consistency might become difficult").
- "More complex object identity. Role objects introduce a logical identity next to the physical identity of objects... you have to introduce a dedicated operation" to compare two role references for logical, rather than physical, sameness.

## 11. Failure modes and misuse

Role identity confusion is the primary source's own most developed misuse, quoted at length because the language is precise: "Role objects introduce a logical identity next to the physical identity of objects. The physical identity is the identity of each individual object. The logical identity is the identity of the logical object consisting of the core and its roles. For each role, you need to be able to ask whether it is physically identical with another role (same object), and whether it is logical identical with another role (which may be another role of the same logical object)... for implementing the logical identity check, you have to introduce a dedicated operation." Worked through concretely: "a client application which works directly with the core object through the Component interface, and refers to its single role instance using a concrete role interface... the two references do not point to the same object because they reference two technically distinct objects. Thus, to find out that the two references are actually denote the same conceptual object, the client must use special identity comparison operations." The concrete symptom is a silent false negative, not a crash. Two references to what is logically the same customer, obtained via different paths, compare unequal under a language's default reference equality, and this most often surfaces as duplicate entries in a deduplicated list or a set membership check, never as an obvious error.

Unsafe or silently absent role retrieval. The paper's own C++ sample requires an explicit down-cast plus a null check, and nothing in the protocol forces the caller to perform it. This mirrors exactly the failure mode the sibling extension-object entry documents for Eclipse's `getAdapter` and C#'s `IServiceProvider.GetService`. The iluwatar Java implementation demonstrates the modern fix (a class token plus `Optional<T>`), but the underlying risk is real for any implementation, in any language, that hands back a plain nullable reference from its role query.

Unenforced role interdependency, quoted directly: "Constraints on roles cannot be enforced by the type system. You might want to exclude certain roles from being attached to the same core object in combination. Or, certain roles may depend on the existence of others. With the Role Object pattern, you can't rely on the type system to enforce the constraints for you. You will have to use runtime checks instead." The paper's own two mitigations: a two-phase-commit-style protocol that asks every role first before finally executing a request, and recursively re-applying the pattern itself so a dependency such as "Borrower requires Customer" is enforced structurally, by nesting Customer as a role of a more general Person core, rather than checked by hand at runtime.

Deleting a shared role object. Quoted directly: "Role objects are safely attached to their core object, once they have been created. They may stick around as long as the core object exists, even if all Clients are long gone... A Client should never delete a Role object, because it never knows whether other Clients are making use of it." Because roles are shared and owned by the core, a client that deletes or frees a role out of habit, the way it might free objects it created itself, produces a use-after-free hazard in a non-garbage-collected language, and a silent bug in a garbage-collected one if detaching is read loosely as ownership transfer.

Role proliferation is not named under this label by the primary source, but it is a direct, reasoned consequence of two things the source does state: roles can be added and removed at runtime with no compile-time ceiling on how many role classes accumulate, and Fowler's own decision guide names "a lot of roles" or "often get new roles" as precisely the condition under which he reaches for Role Object over Role Subtype. A system that keeps adding narrow, one-off role classes to avoid touching a core interface can trade a small core for a bloated set of near-duplicate role classes instead, and this is engineering judgement rather than a sourced claim.

## 12. Trade-off matrix

Two genuinely primary, dated sources exist for this dimension: the pattern's own Applicability section (quoted above under dimension 4) and Martin Fowler's contemporaneous 1997 paper "Dealing with Roles," which is itself built as a decision guide across five named alternatives, one of which is Role Object, described in the authors' own vocabulary and citing them by name. Fowler's own decision text, quoted directly: "Are the role significantly different? If the differences are minor then I use Single Role Type... Are there any common behaviors between the roles? If not I might go for Separate Role Type... Only if I know I have significant common and shared behavior, and I need to [guarantee] integrety [sic] do I need to go to the heavyweight options. Here often the key decision is between Role Subtype and Role Object... Three indicators suggest Role Subtype: there aren't too many roles, new roles do not appear often, and there are significant rules about what combinations and migrations of roles that can occur. If those forces are present then I go with Role Subtype... I would choose Role Object when either I have a lot of roles, or I often get new roles."

| Approach | Role assignment | Client compile-time safety | Identity transparency | Interdependent roles |
|---|---|---|---|---|
| Role Object | Dynamic, attached and detached at runtime, per the pattern's own applicability list | Low with a bare string key (the original C++ sample), higher with a class token plus `Optional` (iluwatar's Java) | Weak by default; the pattern's own authors state a client must use "special identity comparison operations," comparing core references, to know two role references denote the same logical object | Explicitly discouraged by the pattern's own non-applicability line; its own fallback is a runtime two-phase-commit-style check or recursive re-application of the pattern itself |
| Extension Object | Dynamic, queried by name or type token, no transparent wrapping | Low with a string key, higher with a generic class token (Eclipse's `getAdapter`) | Not addressed by Gamma's own paper as a distinct concern the way Role Object's authors address it | Not named as a concern in Gamma's own paper |
| Role Interface and Role Subtype (Fowler) | Static, fixed at compile time | High, ordinary compiler-checked dispatch | Not a concern; there is exactly one physical object playing the role | Well suited, per Fowler's own guide, to a case with "significant rules about what combinations and migrations of roles that can occur" |
| Plain subclassing, the option the paper's own Motivation section rejects | Static, one class per role combination | High, ordinary virtual dispatch | Broken in the way the paper's own Motivation section names, since two objects of different subclasses are never identical, and a polymorphic search must de-duplicate the same logical customer appearing more than once | Combinatorial explosion under multiple inheritance, which the pattern's own first-listed positive consequence is framed as avoiding |

This table is this entry's own synthesis, combining the separately sourced facts above; it should be read as synthesis rather than a single quoted source, the same posture the sibling extension-object entry takes for its own trade-off table.

## 13. Related and incompatible patterns

Decorator, quoted directly from the paper's own comparison: "The Decorator pattern [Gamma+95] has a similar structure but different behavior. The Decorator pattern lets developers chain Decorators around one core, while the Role Object pattern does not allow this. Also, Decorators typically do not extend the core functionality, while Role Objects introduce new operations." Two precise differences, from the pattern's own authors: chaining is disallowed here (each role wraps the core directly, never another role), and Role Object exists specifically to introduce new, client-specific operations, where classic Decorator augments an already-known interface transparently.

Extension Object is the comparison this entry treats as load-bearing, since the two patterns are easy to confuse and address an overlapping stated problem. Quoted directly, in full: "The Extension Object pattern [Gamma97] addresses the same issue: A component is extended by means of extension objects in such a way that they satisfies context-specific requirements. The pattern, however, does not show how Component and ComponentRole objects can be treated transparently, which we consider a key aspect of applying the Role Object pattern. [Also], the Extension Object pattern only touches the issue of extension object (role object) creation and management. We view the integration of the Decorator pattern with the Product Trader pattern to be a key part of the Role Object pattern." The bibliography entry the paper cites for [Gamma97] reads "Erich Gamma. 'Extension Object.' In [Martin+97]. Chapter 6," which is Robert C. Martin, Dirk Riehle, and Frank Buschmann (editors), Pattern Languages of Program Design 3, Addison-Wesley, 1997, the same Chapter 6 attribution this catalogue's own extension-object entry carries. Two concrete, sourced differences follow from that quote. Transparency: a Role Object literally wraps and forwards to its core, so it can stand in wherever the core's own interface is expected, where Extension Object's queried extensions are typically consumed through their own separate interface rather than the subject's own. Creation and management depth: Extension Object's own paper touches role creation and management only lightly, where Role Object folds in a second named pattern, Product Trader, to solve that half of the problem explicitly. The paper also names a real case of the two ideas being conflated in the wild: "The Extension Object pattern has been used for role modeling purposes by Zhao and Foster [Zhao+97] and Schoenfeld [Schoenfeld96]. Zhao and Foster discuss role objects as extension objects, that is they do not transparently wrap the core object... Schoenfeld chose the same primary example as we did, Person and its roles, but also uses the Extension Objects pattern rather than transparently wrapping the core by a Decorator." Two other authors, in other words, solved the identical Person-and-its-roles problem using Extension Object's shape, and the Role Object authors flag that by name as not what they mean by a role object.

The Post pattern, a related but distinct variant: "The Post pattern in [Fowler96] describes an interesting variant of this pattern. Similar to the Extension Object pattern, it describes the responsibilities of a core object in the context of a particular application. However, a Post object exists independently of the core and can live on without being assigned to a core." The citation is Martin Fowler, Analysis Patterns, Addison-Wesley, 1996; this entry did not independently re-verify the Post pattern's own text and attributes the claim to the Role Object paper's own citation.

Type Object, cited as a technique for choosing better specification objects rather than as a competing pattern: "In such situations you can use Type Objects [Johnson+97] as specifications. The core can then retrieve the requested role object by evaluating sub/super type relations," citing Ralph Johnson and Bobby Woolf, "Type Object," in Martin, Riehle, Buschmann (editors), Pattern Languages of Program Design 3, Addison-Wesley, 1997, Chapter 4.

Product Trader, the pattern Role Object explicitly composes with for role creation and management: Dirk Baeumer and Dirk Riehle, "Product Trader," in Martin, Riehle, Buschmann (editors), Pattern Languages of Program Design 3, Addison-Wesley, 1997, Chapter 3.

Fowler's Role Interface and Role Subtype family. Martin Fowler's own 1997 working paper "Dealing with Roles" is very likely the paper the Role Object authors cite in their own References as "Fowler97: Martin Fowler. 'Role Patterns.' Submitted to PLoP '97," though this entry could not independently confirm the two titles name the same document and treats the identity as probable rather than confirmed. That paper sketches a lighter, own-named "Role Object" as one of five options in a decision table, explicitly deferring to the Baeumer/Riehle/Siberski/Wulf paper for the fully transparent version. It places what would later become Fowler's much shorter, separate "Role Interface" bliki entry (dated 22 December 2006, nine years later, with no cross-reference to this paper or to Riehle anywhere on the page) inside a different family entirely, Role Subtype, described by Fowler as compile-time and hidden from callers: "When using Role Subtype with State Object, the state objects are entirely hidden from the user of the class... When using Role Object, however, the user asks the person object for its manager role, and then asks that role for the budget. In other words the roles are public knowledge." Role Interface, in other words, is a separate, later, static interface-segregation technique that shares a name with part of this family but is not itself a Role Object variant. Fowler's own pattern card for Role Object specifically, quoted directly: "How do you represent the many roles of an object? Put common features on a host object with a separate object for each role. Clients ask the host object for the appropriate role to use a role's features. Direct implementation. If you add a new role you don't have to change the host's interface. Awkward if roles have constraint. Exposes role structure to clients of the host object."

No source found names an incompatibility between Role Object and another named pattern; the closest is the non-applicability line under dimension 4, which is a condition on when to reach for the pattern rather than a conflict with a different pattern already in use.

## 14. Refactoring path in and out

Refactoring in is directly grounded in the paper's own Motivation section, itself framed as a before-and-after scenario. The trigger the paper names is a class serving multiple client contexts whose needs would otherwise be folded directly into one interface. The steps below are this entry's own reconstruction from the paper's described Structure and Implementation, not a quoted step-by-step from the source.

1. Factor the existing bloated class's stable, universally needed operations out into an abstract interface, the paper's `Component`.
2. Move the current concrete implementation behind that interface into a `ComponentCore`, and add the role-management protocol (`addRole`, `removeRole`, `hasRole`, `getRole`) to the shared interface, implemented here.
3. Introduce an abstract `ComponentRole` that also implements the shared interface, holding a reference to the core and forwarding every operation to it.
4. Pull each client-specific slice of the old bloated interface into its own `ConcreteRole` subclass, matching the paper's own `Borrower`/`Investor` split by department.
5. Where the set of roles must be extensible by code that does not own the core class, add a creation and lookup mechanism decoupled from any specific role class, the paper's own Product Trader, or a simpler closed-set alternative such as iluwatar's enum-of-role-classes.

Refactoring out has two directions with real sourcing behind each, matching Fowler's own decision-guide framing exactly.

Toward Role Subtype, when the role set stabilizes to a small, known, closed set, quoted directly from Fowler's own decision text: "Three indicators suggest Role Subtype: there aren't too many roles, new roles do not appear often, and there are significant rules about what combinations and migrations of roles that can occur. If those forces are present then I go with Role Subtype." Fowler's own stated trade: collapsing to Role Subtype presents a simpler interface to every client at the cost of a harder implementation once, in exchange for the pattern's own second-named liability, "clients are likely to get more complex," disappearing entirely, since role membership becomes an implementation detail hidden behind the host object rather than something every client must query for and cast.

Toward the pattern's own recursive-composition mitigation, when the problem is not role-set stability but unenforced interdependency between roles. Rather than abandoning Role Object, the primary source's own recursive-application material (dimension 7) shows re-modeling the dependent role itself as a further key abstraction with its own roles, so a structural precondition, Borrower requires Customer, becomes a structural guarantee rather than a hand-written runtime check. This is a narrower refactor into a better-structured form of the same pattern, not a refactor to a different pattern.

A third, weakly sourced direction is worth naming rather than asserting: collapsing to Extension Object's queried, non-wrapping shape once transparency is no longer needed by any client. The primary source names two other authors, Zhao and Foster, and Schoenfeld, who chose Extension Object over Role Object for structurally similar problems, which implies this direction by analogy, but neither the Role Object paper nor Extension Object's own paper states it as a named refactoring technique in either direction; it is this entry's own inference, not a sourced step.

## 15. Testing and verification

No source found addresses testing strategy for Role Object specifically; this entire dimension is engineering reasoning drawn directly from the structure the sources above describe, stated as judgement rather than dressed as fact.

The role-query method, `getRole` or `hasRole`, or iluwatar's `Optional<T> getRole(Role, Class<T>)`, is the natural seam for a test double. Code that consumes a role-bearing object can be tested against a minimal fake core implementing only that query, asserting behavior for both a present role and an absent one, without constructing the full core-plus-registry object graph a real `CustomerCore` would require.

The absent case deserves its own explicit test, for a reason grounded directly in the sources. The primary paper's own Collaborations section states the miss-handling contract is implementation-defined: "an exception is thrown or an error is reported." A consuming test suite cannot assume one universal contract and must exercise whichever one the concrete implementation under test actually chose.

Each `ConcreteRole` class is independently testable in isolation, guaranteed by the pattern's own participant design: a `BorrowerRole` or `InvestorRole` is a small, focused class answering to a narrow interface, so it can be constructed and exercised directly in a unit test without going through `Customer` or `CustomerCore` at all, wherever the concrete role's own constructor does not require a live core reference.

Role addition and removal are stateful operations on the core and deserve explicit round-trip tests: adding a role makes `hasRole`/`getRole` for that role subsequently succeed; removing a role, where the implementation supports it, makes it subsequently fail or return empty; and a role which was never added is never instantiated at all, directly observable in the iluwatar code since `Role.instance()` is only invoked from inside `CustomerCore.addRole`.

Logical identity, where the implementation provides an explicit identity-comparison operation per the pattern's own Consequences text, is itself a testable contract and a natural place for a regression test, since the pattern's own authors name this as a place where a naive equality check silently gives the wrong answer.

## 16. Observability signals

No source found for this entry addresses observability for Role Object directly, and this dimension is entirely engineering judgement, stated as such rather than as a sourced fact.

The signal most specific to this pattern is a count of role queries that return a miss (an exception, an error code, or an empty result, depending on the implementation's own choice per dimension 7) against the total number of role queries, broken down by the requested role. A healthy system shows this ratio stable and low for a role the caller genuinely expected to be present. A rising miss rate against one particular role points at either a real capability gap, a core object that was never given the role a client now needs, or a client that has stopped checking `hasRole` before calling `getRole`, which is itself the unsafe-retrieval failure mode named in dimension 11.

A second signal, drawn directly from the pattern's own Consequences text, is the rate of role attachment and detachment relative to core object lifetime. The paper states roles are only created "when they are needed in a given situation," so a core object accumulating an unusually large number of distinct roles over its lifetime is an observable, countable proxy for the role-proliferation risk named in dimension 11, and is worth graphing per core object type over time.

A third, cheaper signal, available with no pattern-specific instrumentation at all, is watching for a class-cast or type exception whose stack trace originates immediately after a role query. Because the paper's own C++ sample requires an explicit down-cast with no compiler-enforced check, and only the more modern, type-safe variants (dimension 8) close that gap, a cluster of such exceptions around one role type is a direct, observable symptom of the unsafe-retrieval failure mode.

## 17. Security and privacy implications

No source found for this entry addresses security or privacy for Role Object directly, and the reasoning here is analytical rather than sourced.

The most concrete implication follows directly from the pattern's own stated identity-transparency liability (dimension 11). A role query is effectively a capability check: a client that successfully obtains a `Borrower` role, for instance, is implicitly being granted whatever operations that role's interface exposes. Any concrete `ComponentCore` whose `addRole` or `getRole` implementation makes an authorization decision, granting a sensitive role only to some callers, is a security-relevant surface that deserves the same scrutiny as any other access-control code, even though the pattern's own literature never frames it that way. The pattern's own logical-identity confusion (dimension 11) compounds this in a specific way worth naming: if an authorization check compares role references using a language's default reference equality rather than the pattern's own dedicated logical-identity operation, two references to the same underlying customer could be wrongly treated as different principals, or, in the opposite direction, two references that only happen to share a core through an unrelated aliasing bug could be wrongly treated as the same principal.

Role Object carries no data-handling implications of its own beyond whatever state the core and its concrete role objects already carry. It introduces no new storage, no new network surface, and no new serialization boundary on its own; a role class that happens to hold sensitive, context-specific data, the paper's own `Borrower` holding credit and security-account state is exactly this shape, inherits whatever protection the surrounding system already applies to that data, and the pattern itself neither strengthens nor weakens it. Where the pattern's own sources are silent on a security concern, that silence is recorded here rather than an invented one supplied in its place.

## 18. References

Dirk Baeumer, Dirk Riehle, Wolf Siberski, and Martina Wulf. "Role Object." In Neil Harrison, Brian Foote, Hans Rohnert (editors), Pattern Languages of Program Design 4. Addison-Wesley, 2000. Chapter 2, pages 15 to 32. https://www.riehle.org/computer-science/research/2000/plopd-4.pdf. Verified 2026-08-23.

Dirk Baeumer, Dirk Riehle, Wolf Siberski, and Martina Wulf. "The Role Object Pattern." PLoP 97 conference paper, paper 2.1, Technical Report WUCS-97-34, Washington University Department of Computer Science, 1997. https://hillside.net/plop/plop97/Proceedings/riehle.pdf. Verified 2026-08-23.

Dirk Riehle. Research archive landing page for the 1997 conference paper, linking to the 2000 revision. https://www.riehle.org/computer-science/research/1997/plop-1997-role-object.html. Verified 2026-08-23.

Dirk Riehle. Research archive landing page for the 2000 PLoPD4 chapter, linking back to the 1997 conference paper. https://www.riehle.org/computer-science/research/2000/plopd-4.html. Verified 2026-08-23.

Dirk Riehle. Publications list, independently confirming the "Role Object" PLoPD4 citation. https://dirkriehle.com/publications/. Verified 2026-08-23.

Dirk Baeumer, Guido Gryczan, Rolf Knoll, Carola Lilienthal, Dirk Riehle, and Heinz Zuellighoven. "Framework Development for Large Systems." Communications of the ACM 40, no. 10 (October 1997), pages 52 to 59. Cited from the Role Object paper's own Known Uses section as the source for the GEBOS banking system, and independently confirmed to exist with this exact author list via Dirk Riehle's own publications page. https://riehle.org/computer-science/research/1997/cacm-1997-frameworks.html. Verified 2026-08-23.

Kin'ichi Mitsui, Hiroaki Nakamura, Theodore C. Law, and Shahram Javey. "Design of an Integrated and Extensible C++ Programming Environment." Object Technology for Advanced Software (ISOTAS-93, LNCS-742), Springer-Verlag, 1993, pages 95 to 109. Cited from the Role Object paper's own References section for the AST node decoration known use, not independently located as a standalone source. Verified 2026-08-23.

Martin Fowler. "Dealing with Roles." Working draft, 20 July 1997. https://martinfowler.com/apsupp/roles.pdf. Verified 2026-08-23.

Martin Fowler. "RoleInterface." Bliki, 22 December 2006. https://martinfowler.com/bliki/RoleInterface.html. Verified 2026-08-23.

Iluwatar. "Role Object Pattern." java-design-patterns catalogue, reference implementation. https://java-design-patterns.com/patterns/role-object/. Verified 2026-08-23.

Wikipedia. Absence check confirming no dedicated "Role Object pattern" article exists on this site. https://en.wikipedia.org/w/index.php?search=Role+Object+pattern&title=Special:Search&fulltext=1. Verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** The Baeumer, Riehle, Siberski, and Wulf paper was read directly in both its 1997 and 2000 editions, and the two editions' genuine wording differences (the dropped applicability bullet, the dropped "subject" vocabulary) are independently confirmed by a side-by-side read rather than assumed. The pattern's own direct, quotable comparison to Extension Object (dimension 13) is unusually strong sourcing for a related-patterns claim, since design pattern papers rarely name and critique a specific rival paper by title and author this precisely. Martin Fowler's contemporaneous "Dealing with Roles" independently corroborates both the trade-off matrix (dimension 12) and the Role Object/Role Interface distinction (dimension 13) from a second, primary, dated source that cites the Baeumer et al. paper directly by name.

**Unverified or unclear.** Whether Martin Fowler's own "Dealing with Roles" (the document actually fetched and read) is the same document the Role Object paper cites as "Fowler97: Role Patterns, submitted to PLoP 97" is probable but not independently confirmed, since no accessible PLoP 97 proceedings index could be checked. The word "GEBOS" was not independently confirmed to appear inside the full body text of the cited 1997 CACM paper, only in the Role Object paper's own citation of it. The iluwatar catalogue's Java implementation was found to diverge structurally from the paper's own transparent-decorator forwarding mechanic (dimension 8), using inheritance rather than composition, which this entry states plainly rather than smoothing over.

## Code

TypeScript, Python, and Go each model the core-plus-role shape directly, following the paper's own composition-based decorator forwarding rather than iluwatar's inheritance variant. Kotlin and Swift are omitted, since both languages offer a native extension or protocol-conformance mechanism that solves the same underlying need more directly, as covered in dimension 8.

### TypeScript

```typescript
interface Customer {
  name(): string;
  hasRole(role: string): boolean;
  getRole<T extends Customer>(role: string): T | undefined;
}

class CustomerCore implements Customer {
  private roles = new Map<string, ComponentRole>();

  constructor(private readonly customerName: string) {}

  name(): string {
    return this.customerName;
  }

  addRole(role: string, factory: (core: CustomerCore) => ComponentRole): void {
    if (!this.roles.has(role)) {
      this.roles.set(role, factory(this));
    }
  }

  removeRole(role: string): void {
    this.roles.delete(role);
  }

  hasRole(role: string): boolean {
    return this.roles.has(role);
  }

  getRole<T extends Customer>(role: string): T | undefined {
    return this.roles.get(role) as T | undefined;
  }
}

abstract class ComponentRole implements Customer {
  constructor(protected readonly core: CustomerCore) {}

  name(): string {
    return this.core.name();
  }

  hasRole(role: string): boolean {
    return this.core.hasRole(role);
  }

  getRole<T extends Customer>(role: string): T | undefined {
    return this.core.getRole<T>(role);
  }
}

class Borrower extends ComponentRole {
  private securities: string[] = [];

  pledge(security: string): void {
    this.securities.push(security);
  }

  listSecurities(): readonly string[] {
    return this.securities;
  }
}

class Investor extends ComponentRole {
  private portfolioValue = 0;

  deposit(amount: number): void {
    this.portfolioValue += amount;
  }

  balance(): number {
    return this.portfolioValue;
  }
}

const core = new CustomerCore("John Doe");
core.addRole("Borrower", (c) => new Borrower(c));

const borrower = core.getRole<Borrower>("Borrower");
if (borrower) {
  borrower.pledge("municipal-bond-2031");
}
```

### Python

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, TypeVar

T = TypeVar("T", bound="Customer")


class Customer(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def has_role(self, role: str) -> bool: ...

    @abstractmethod
    def get_role(self, role: str) -> Optional["Customer"]: ...


class CustomerCore(Customer):
    def __init__(self, customer_name: str) -> None:
        self._name = customer_name
        self._roles: dict[str, "ComponentRole"] = {}

    def name(self) -> str:
        return self._name

    def add_role(self, role: str, instance: "ComponentRole") -> None:
        self._roles.setdefault(role, instance)

    def remove_role(self, role: str) -> None:
        self._roles.pop(role, None)

    def has_role(self, role: str) -> bool:
        return role in self._roles

    def get_role(self, role: str) -> Optional["Customer"]:
        return self._roles.get(role)


class ComponentRole(Customer):
    def __init__(self, core: CustomerCore) -> None:
        self._core = core

    def name(self) -> str:
        return self._core.name()

    def has_role(self, role: str) -> bool:
        return self._core.has_role(role)

    def get_role(self, role: str) -> Optional["Customer"]:
        return self._core.get_role(role)


class Borrower(ComponentRole):
    def __init__(self, core: CustomerCore) -> None:
        super().__init__(core)
        self._securities: list[str] = []

    def pledge(self, security: str) -> None:
        self._securities.append(security)

    def securities(self) -> list[str]:
        return list(self._securities)


class Investor(ComponentRole):
    def __init__(self, core: CustomerCore) -> None:
        super().__init__(core)
        self._balance = 0.0

    def deposit(self, amount: float) -> None:
        self._balance += amount

    def balance(self) -> float:
        return self._balance


core = CustomerCore("Jane Roe")
core.add_role("Borrower", Borrower(core))

borrower = core.get_role("Borrower")
if isinstance(borrower, Borrower):
    borrower.pledge("corporate-bond-2029")
```

### Go

```go
package roleobject

type Customer interface {
	Name() string
	HasRole(role string) bool
	GetRole(role string) (Customer, bool)
}

type CustomerCore struct {
	name  string
	roles map[string]Customer
}

func NewCustomerCore(name string) *CustomerCore {
	return &CustomerCore{name: name, roles: make(map[string]Customer)}
}

func (c *CustomerCore) Name() string { return c.name }

func (c *CustomerCore) AddRole(role string, instance Customer) {
	if _, exists := c.roles[role]; !exists {
		c.roles[role] = instance
	}
}

func (c *CustomerCore) RemoveRole(role string) {
	delete(c.roles, role)
}

func (c *CustomerCore) HasRole(role string) bool {
	_, ok := c.roles[role]
	return ok
}

func (c *CustomerCore) GetRole(role string) (Customer, bool) {
	r, ok := c.roles[role]
	return r, ok
}

type componentRole struct {
	core *CustomerCore
}

func (r componentRole) Name() string { return r.core.Name() }

func (r componentRole) HasRole(role string) bool { return r.core.HasRole(role) }

func (r componentRole) GetRole(role string) (Customer, bool) { return r.core.GetRole(role) }

type Borrower struct {
	componentRole
	securities []string
}

func NewBorrower(core *CustomerCore) *Borrower {
	return &Borrower{componentRole: componentRole{core: core}}
}

func (b *Borrower) Pledge(security string) {
	b.securities = append(b.securities, security)
}

func (b *Borrower) Securities() []string { return b.securities }

type Investor struct {
	componentRole
	balance float64
}

func NewInvestor(core *CustomerCore) *Investor {
	return &Investor{componentRole: componentRole{core: core}}
}

func (i *Investor) Deposit(amount float64) { i.balance += amount }

func (i *Investor) Balance() float64 { return i.balance }
```
