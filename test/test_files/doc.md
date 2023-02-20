# MyClass docs

MyClass uses a singleton in the backend and asserts single ownership with the `create` and `release` functions.
<!-- @claim{MyClass/create/docs} single instance at a time -->

Usage:

```cpp
{
    auto objPtr = MyClass::create();
    // auto objPtr2 = MyClass::create(); <-- this would throw

    obj.initialize();
    obj.execute();
    // ...

    MyClass::release(objPtr);
    // another instance can be created here, after release
    auto objPtr2 = MyClass::create();
}
```