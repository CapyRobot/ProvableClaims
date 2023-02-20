#pragma once

class MyClass
{
public:
    MyClass() = delete;

    /// @brief ...
    /// @return ...
    static MyClass *create()
    {
        // @proof{MyClass/create/docs} single instance at a time
        // ... check if we are creating a second instance ...

        MyClass *ptr{nullptr};
        /* ... */
        return ptr;
    };
    static void release(MyClass *){/* ... */};

    /// @brief initialize my class instance
    /// @throws std::logic_error if the instance has already been initialized
    /// @claim{MyClass/initialize} logic_error on double init
    void initialize();

    /// @brief ...
    void execute(){/* ... */};
};